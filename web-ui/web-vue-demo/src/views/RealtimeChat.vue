<template>
  <div class="realtime-chat">
    <div class="page-header">
      <router-link to="/" class="back-btn">← 返回首页</router-link>
      <h1>🚀 实时语音对话</h1>
      <p>完整的实时语音交互体验，语音转录 → LLM对话 → 语音合成</p>
    </div>

    <div class="realtime-voice-chat">
      <div class="controls">
        <button @click="startChat" :disabled="isRecording" class="start-btn">开始对话</button>
        <button @click="stopChat" :disabled="!isRecording" class="stop-btn">停止对话</button>
        <button @click="manualSendAudio" :disabled="!isRecording || audioBuffer.length === 0" class="manual-btn">立即发送音频 ({{ audioBuffer.length }})</button>
        <span v-if="isRecording" class="recording-dot"></span>
      </div>
      <div class="status-indicators">
        <div class="vad-indicator">
          <span :class="vadState === '说话中' ? 'vad-on' : 'vad-off'">
            {{ vadState }}
          </span>
        </div>
        <div class="processing-status">
          <span v-if="isTranscribing" class="status-item">📝 转录中...</span>
          <span v-if="isLLMProcessing" class="status-item">🧠 思考中...</span>
          <span v-if="isTTSProcessing" class="status-item">🎵 合成中...</span>
        </div>
      </div>
      <div class="chat-history">
        <div v-for="(msg, idx) in history" :key="idx" :class="['msg-bubble', msg.role, (msg.role==='bot' && idx===currentPlayingIdx) ? 'playing' : '']">
          <span v-if="msg.role==='user'">🧑‍💬</span>
          <span v-else-if="msg.role==='asr'">📝</span>
          <span v-else-if="msg.role==='system'">⚙️</span>
          <span v-else>🤖</span>
          <span class="msg-text">{{ msg.text }}</span>
        </div>
      </div>
      <div class="audio-status">
        <span v-if="isPlaying" class="playing-indicator">🔊 正在播放回复音频...</span>
        <span v-else-if="audioQueue.length > 0" class="queue-indicator">📋 音频队列: {{ audioQueue.length }} 个片段</span>
      </div>
      <div v-if="errorMessage" class="error-message">
        ⚠️ {{ errorMessage }}
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick, onUnmounted } from 'vue'
import Recorder from 'recorder-core'
import 'recorder-core/src/engine/wav'

const isRecording = ref(false)
const history = ref([])
const vadState = ref('静音') // VAD状态
const audioQueue = ref([])
const isPlaying = ref(false)
const currentPlayingIdx = ref(-1) // 当前正在播放的bot消息索引
const errorMessage = ref('')

// 新增状态指示
const isTranscribing = ref(false)
const isLLMProcessing = ref(false)
const isTTSProcessing = ref(false)

// VAD改进：使用更宽松的参数
let silenceTimer = null
let lastPowerLevel = 0
let silenceStartTime = 0
const SILENCE_THRESHOLD = 5 // 降低静音阈值，更容易检测到说话
const SILENCE_DURATION = 500 // 降低静音检测时长，更快响应
const MIN_SPEECH_DURATION = 200 // 降低最小说话时长

// 录音缓冲区管理 - 优化
let audioBuffer = []
let isBuffering = false
const MAX_BUFFER_SIZE = 20 // 与后端config保持一致
let speechStartTime = 0

// 资源管理
let rec = null
let ws = null
let sendTimer = null
let currentAudio = null
let audioUrls = new Set() // 跟踪所有创建的audio URL
let connectionRetryCount = 0
const maxRetryCount = 3

// 新增：音频质量检测和预处理
let audioQualityStats = {
  averagePowerLevel: 0,
  peakPowerLevel: 0,
  silenceRatio: 0,
  sampleCount: 0
}

// 新增：连接质量监控
let connectionQuality = {
  latency: 0,
  lastPingTime: 0,
  avgLatency: 0,
  pingCount: 0
}

// 新增：自动调节参数
let adaptiveParams = {
  dynamicSilenceDuration: SILENCE_DURATION,
  dynamicSilenceThreshold: SILENCE_THRESHOLD,
  isAdaptive: true
}

function addMsg(role, text) {
  history.value.push({ role, text })
  nextTick(() => {
    const el = document.querySelector('.chat-history')
    if (el) el.scrollTop = el.scrollHeight
  })
}

function clearError() {
  errorMessage.value = ''
}

function showError(error) {
  errorMessage.value = error
  console.error('Error:', error)
}

function cleanupAudioUrls() {
  // 清理所有创建的音频URL
  audioUrls.forEach(url => {
    try {
      URL.revokeObjectURL(url)
    } catch (e) {
      console.warn('Failed to revoke URL:', e)
    }
  })
  audioUrls.clear()
}

function stopCurrentAudio() {
  if (currentAudio) {
    currentAudio.pause()
    currentAudio.currentTime = 0
    currentAudio = null
  }
}

function cleanupRecorder() {
  if (rec) {
    try {
      rec.close()
    } catch (e) {
      console.warn('Failed to close recorder:', e)
    }
    rec = null
  }
}

function cleanupTimer() {
  if (sendTimer) {
    clearInterval(sendTimer)
    sendTimer = null
  }
  if (silenceTimer) {
    clearTimeout(silenceTimer)
    silenceTimer = null
  }
}

function cleanupWebSocket() {
  if (ws) {
    try {
      if (ws.readyState === WebSocket.OPEN) {
        ws.close()
      }
    } catch (e) {
      console.warn('Failed to close WebSocket:', e)
    }
    ws = null
  }
}

function fullCleanup() {
  cleanupTimer()
  cleanupRecorder()
  stopCurrentAudio()
  cleanupAudioUrls()
  cleanupWebSocket()
  
  isRecording.value = false
  vadState.value = '静音'
  audioQueue.value = []
  isPlaying.value = false
  currentPlayingIdx.value = -1
  connectionRetryCount = 0
  audioBuffer = []
  isBuffering = false
  speechStartTime = 0
  
  // 重置状态指示
  isTranscribing.value = false
  isLLMProcessing.value = false
  isTTSProcessing.value = false
}

function updateAudioQualityStats(powerLevel) {
  audioQualityStats.sampleCount++
  
  // 更新平均音量
  audioQualityStats.averagePowerLevel = 
    (audioQualityStats.averagePowerLevel * (audioQualityStats.sampleCount - 1) + powerLevel) / audioQualityStats.sampleCount
  
  // 更新峰值音量
  if (powerLevel > audioQualityStats.peakPowerLevel) {
    audioQualityStats.peakPowerLevel = powerLevel
  }
  
  // 计算静音比例
  if (powerLevel <= SILENCE_THRESHOLD) {
    audioQualityStats.silenceRatio = 
      (audioQualityStats.silenceRatio * (audioQualityStats.sampleCount - 1) + 1) / audioQualityStats.sampleCount
  } else {
    audioQualityStats.silenceRatio = 
      (audioQualityStats.silenceRatio * (audioQualityStats.sampleCount - 1) + 0) / audioQualityStats.sampleCount
  }
  
  // 自适应调整参数
  if (adaptiveParams.isAdaptive && audioQualityStats.sampleCount > 50) {
    // 如果环境比较安静，降低静音阈值
    if (audioQualityStats.averagePowerLevel < 5 && audioQualityStats.silenceRatio > 0.8) {
      adaptiveParams.dynamicSilenceThreshold = Math.max(3, SILENCE_THRESHOLD - 2)
    }
    // 如果环境比较嘈杂，提高静音阈值
    else if (audioQualityStats.averagePowerLevel > 20) {
      adaptiveParams.dynamicSilenceThreshold = SILENCE_THRESHOLD + 5
    }
    
    // 根据用户说话习惯调整静音检测时长
    if (audioQualityStats.silenceRatio < 0.3) {
      // 用户说话频繁，缩短静音检测时间
      adaptiveParams.dynamicSilenceDuration = Math.max(300, SILENCE_DURATION - 200)
    }
  }
}

function measureLatency() {
  if (ws && ws.readyState === WebSocket.OPEN) {
    connectionQuality.lastPingTime = Date.now()
    // 发送JSON格式的ping消息，避免与音频数据冲突
    ws.send(JSON.stringify({type: 'ping', timestamp: connectionQuality.lastPingTime}))
  }
}

function connectWebSocket() {
  return new Promise((resolve, reject) => {
    try {
      ws = new WebSocket('ws://127.0.0.1:8000/api/v1/ws/realtime')
      ws.binaryType = 'arraybuffer'
      
      const connectionTimeout = setTimeout(() => {
        if (ws.readyState !== WebSocket.OPEN) {
          reject(new Error('WebSocket连接超时'))
        }
      }, 5000)
      
      ws.onopen = () => {
        clearTimeout(connectionTimeout)
        console.log('WebSocket连接已建立')
        connectionRetryCount = 0
        clearError()
        
        // 开始定期测量延迟
        setInterval(measureLatency, 5000)
        
        resolve()
      }
      
      ws.onmessage = (event) => {
        try {
          if (typeof event.data === 'string') {
            const msg = JSON.parse(event.data)
            if (msg.error) {
              showError(msg.error)
              console.error('服务器错误:', msg.error)
              return
            }
            if (msg.type === 'ping') {
              // 处理ping响应，计算延迟
              if (connectionQuality.lastPingTime > 0) {
                const latency = Date.now() - connectionQuality.lastPingTime
                connectionQuality.latency = latency
                connectionQuality.pingCount++
                connectionQuality.avgLatency = 
                  (connectionQuality.avgLatency * (connectionQuality.pingCount - 1) + latency) / connectionQuality.pingCount
                
                console.log(`WebSocket延迟: ${latency}ms, 平均延迟: ${connectionQuality.avgLatency.toFixed(1)}ms`)
                
                // 根据延迟调整参数
                if (connectionQuality.avgLatency > 500) {
                  adaptiveParams.dynamicSilenceDuration = Math.max(SILENCE_DURATION, SILENCE_DURATION + 300)
                } else if (connectionQuality.avgLatency < 200) {
                  adaptiveParams.dynamicSilenceDuration = Math.max(300, SILENCE_DURATION - 200)
                }
              }
              return
            }
            if (msg.type === 'transcription') {
              isTranscribing.value = false
              console.log('收到转录结果:', msg.text)
              if (msg.text) {
                addMsg('asr', msg.text)
                isLLMProcessing.value = true
              }
            }
            if (msg.type === 'llm') {
              isLLMProcessing.value = false
              isTTSProcessing.value = true
              console.log('收到LLM回复:', msg.text)
              addMsg('bot', msg.text)
            }
          } else {
            // 收到TTS音频流，加入队列
            isTTSProcessing.value = false
            console.log('收到TTS音频数据，大小:', event.data.byteLength)
            const blob = new Blob([event.data], { type: 'audio/wav' })
            audioQueue.value.push(blob)
            playNextAudio()
          }
        } catch (e) {
          console.error('处理WebSocket消息失败:', e)
          showError('消息处理失败')
        }
      }
      
      ws.onclose = (event) => {
        clearTimeout(connectionTimeout)
        console.log('WebSocket连接已关闭', event.code, event.reason)
        
        if (isRecording.value && connectionRetryCount < maxRetryCount) {
          // 尝试重连
          connectionRetryCount++
          console.log(`尝试重连 ${connectionRetryCount}/${maxRetryCount}`)
          setTimeout(() => {
            if (isRecording.value) {
              startChat()
            }
          }, 1000 * connectionRetryCount)
        } else {
          fullCleanup()
          if (connectionRetryCount >= maxRetryCount) {
            showError('连接失败，请检查服务器状态')
          }
        }
      }
      
      ws.onerror = (error) => {
        clearTimeout(connectionTimeout)
        console.error('WebSocket错误:', error)
        showError('WebSocket连接错误')
        reject(error)
      }
    } catch (e) {
      reject(e)
    }
  })
}

async function startChat() {
  try {
    fullCleanup()
    history.value = []
    
    await connectWebSocket()
    await initRecorder()
  } catch (error) {
    console.error('启动聊天失败:', error)
    showError('启动失败: ' + error.message)
    fullCleanup()
  }
}

function initRecorder() {
  return new Promise((resolve, reject) => {
    try {
      rec = new Recorder({
        type: 'wav',
        sampleRate: 16000,
        bitRate: 16,
        connectWebM: false,
        connectEnableWebM: false,
        onProcess(buffers, powerLevel, bufferDuration, bufferSampleRate, newBufferIdx, asyncEnd) {
          const currentTime = Date.now()
          
          // 更新音频质量统计
          updateAudioQualityStats(powerLevel)
          
          // 使用自适应参数
          const currentSilenceThreshold = adaptiveParams.dynamicSilenceThreshold
          const currentSilenceDuration = adaptiveParams.dynamicSilenceDuration
          
          // 改进的VAD检测
          if (powerLevel > currentSilenceThreshold) {
            if (vadState.value !== '说话中') {
              console.log(`🗣️ 检测到说话开始，音量: ${powerLevel}, 阈值: ${currentSilenceThreshold}`)
              vadState.value = '说话中'
            }
            
            // 记录说话开始时间
            if (speechStartTime === 0) {
              speechStartTime = currentTime
              console.log(`📅 说话开始时间记录: ${speechStartTime}`)
            }
            
            // 如果从静音转为说话，清除静音计时器
            if (silenceTimer) {
              clearTimeout(silenceTimer)
              silenceTimer = null
            }
            silenceStartTime = 0
          } else {
            if (vadState.value !== '静音') {
              console.log(`🤫 检测到静音开始，音量: ${powerLevel}, 阈值: ${currentSilenceThreshold}`)
              vadState.value = '静音'
            }
            
            // 如果刚开始静音，记录时间
            if (silenceStartTime === 0 && speechStartTime > 0) {
              silenceStartTime = currentTime
              console.log(`⏰ 静音开始时间记录: ${silenceStartTime}`)
            }
            
            // 如果静音持续一定时间，且之前有足够长的说话，则发送缓冲的音频
            if (silenceStartTime > 0 && 
                speechStartTime > 0 &&
                currentTime - silenceStartTime >= currentSilenceDuration && 
                currentTime - speechStartTime >= MIN_SPEECH_DURATION &&
                audioBuffer.length > 0 && 
                !isBuffering) {
              const speechDuration = currentTime - speechStartTime
              const silenceDuration = currentTime - silenceStartTime
              console.log(`🚀 自适应VAD触发发送: 说话时长=${speechDuration}ms, 静音时长=${silenceDuration}ms, 缓冲区=${audioBuffer.length}个片段`)
              sendBufferedAudio()
            }
          }
          
          lastPowerLevel = powerLevel
        }
      })
      
      rec.open(() => {
        console.log('录音器已打开')
        // 重置音频质量统计
        audioQualityStats = {
          averagePowerLevel: 0,
          peakPowerLevel: 0,
          silenceRatio: 0,
          sampleCount: 0
        }
        startContinuousRecording()
        resolve()
      }, (msg, isUserNotAllow) => {
        const errorMsg = isUserNotAllow ? '用户拒绝了麦克风权限' : `无法录音: ${msg}`
        console.error('录音器打开失败:', msg, isUserNotAllow)
        showError(errorMsg)
        reject(new Error(errorMsg))
      })
    } catch (e) {
      reject(e)
    }
  })
}

function sendBufferedAudio() {
  if (audioBuffer.length === 0 || !ws || ws.readyState !== WebSocket.OPEN || isBuffering) {
    console.warn('无法发送音频:', {
      bufferLength: audioBuffer.length,
      wsState: ws?.readyState,
      isBuffering
    })
    return
  }
  
  isBuffering = true
  isTranscribing.value = true
  
  // 合并所有缓冲的音频
  const totalLength = audioBuffer.reduce((sum, buffer) => sum + buffer.byteLength, 0)
  const mergedBuffer = new Uint8Array(totalLength)
  let offset = 0
  
  audioBuffer.forEach(buffer => {
    mergedBuffer.set(new Uint8Array(buffer), offset)
    offset += buffer.byteLength
  })
  
  // 发送合并后的音频
  ws.send(mergedBuffer.buffer)
  console.log('🎵 发送合并音频，总大小:', totalLength, '字节，包含', audioBuffer.length, '个分片')
  addMsg('system', `发送音频: ${totalLength} 字节 (${audioBuffer.length} 分片)`)
  
  // 清空缓冲区
  audioBuffer = []
  silenceStartTime = 0
  speechStartTime = 0
  
  setTimeout(() => {
    isBuffering = false
  }, 200)
}

function manualSendAudio() {
  console.log('🎯 手动发送音频')
  sendBufferedAudio()
}

function startContinuousRecording() {
  if (!rec || isRecording.value) return
  
  isRecording.value = true
  
  const recordAndBuffer = () => {
    if (!rec || !isRecording.value || !ws || ws.readyState !== WebSocket.OPEN) {
      return
    }
    
    rec.start()
    console.log('开始录音')
  }
  
  // 使用与后端config一致的录音间隔 (500ms)
  sendTimer = setInterval(() => {
    if (rec && isRecording.value && ws && ws.readyState === WebSocket.OPEN) {
      rec.stop((blob) => {
        console.log('录音分片完成，大小:', blob.size)
        if (blob.size > 0) {
          // 将音频加入缓冲区而不是立即发送
          blob.arrayBuffer().then(buf => {
            audioBuffer.push(buf)
            // 限制缓冲区大小，防止内存溢出
            if (audioBuffer.length > MAX_BUFFER_SIZE) {
              audioBuffer.shift() // 移除最旧的音频数据
              console.log('音频缓冲区已满，移除最旧数据')
            }
          }).catch(err => {
            console.error('处理音频分片失败:', err)
          })
        }
        // 立即重新开始录音，确保连续性
        setTimeout(() => {
          if (rec && isRecording.value) {
            rec.start()
            console.log('重新开始录音')
          }
        }, 10)
      }, (msg) => {
        console.warn('导出分片失败:', msg)
        showError('录音处理失败')
        // 出错后也要重新开始录音
        setTimeout(() => {
          if (rec && isRecording.value) {
            rec.start()
            console.log('录音出错后重新开始')
          }
        }, 100)
      })
    }
  }, 500) // 500ms间隔
  
  recordAndBuffer()
}

function playNextAudio() {
  if (isPlaying.value || audioQueue.value.length === 0) return
  
  isPlaying.value = true
  
  // 找到下一个bot消息的索引
  const nextBotIdx = history.value.findIndex((msg, idx) =>
    msg.role === 'bot' && idx > currentPlayingIdx.value
  )
  if (nextBotIdx !== -1) {
    currentPlayingIdx.value = nextBotIdx
  }
  
  const blob = audioQueue.value.shift()
  const url = URL.createObjectURL(blob)
  audioUrls.add(url) // 跟踪URL以便后续清理
  
  stopCurrentAudio() // 停止当前播放的音频
  currentAudio = new Audio(url)
  
  // 减少音频播放延迟
  currentAudio.preload = 'auto'
  
  currentAudio.onended = () => {
    isPlaying.value = false
    
    // 清理当前音频URL
    try {
      URL.revokeObjectURL(url)
      audioUrls.delete(url)
    } catch (e) {
      console.warn('Failed to revoke audio URL:', e)
    }
    
    currentAudio = null
    
    // 更快播放下一个音频
    setTimeout(() => playNextAudio(), 20)
  }
  
  currentAudio.onerror = (e) => {
    console.error('音频播放失败:', e)
    isPlaying.value = false
    currentAudio = null
    
    // 清理失败的音频URL
    try {
      URL.revokeObjectURL(url)
      audioUrls.delete(url)
    } catch (e) {
      console.warn('Failed to revoke audio URL:', e)
    }
    
    // 尝试播放下一个
    setTimeout(() => playNextAudio(), 20)
  }
  
  currentAudio.play().catch(e => {
    console.error('音频播放启动失败:', e)
    showError('音频播放失败')
  })
}

function stopChat() {
  console.log('停止对话')
  fullCleanup()
}

// 组件卸载时清理资源
onUnmounted(() => {
  fullCleanup()
})

// 页面隐藏时暂停，显示时恢复
document.addEventListener('visibilitychange', () => {
  if (document.hidden && isRecording.value) {
    // 页面隐藏时暂停录音但不关闭连接
    cleanupTimer()
    cleanupRecorder()
    vadState.value = '静音'
  } else if (!document.hidden && ws && ws.readyState === WebSocket.OPEN && isRecording.value) {
    // 页面显示时恢复录音
    initRecorder().catch(e => {
      console.error('恢复录音失败:', e)
      showError('恢复录音失败')
    })
  }
})
</script>

<style scoped>
.realtime-chat {
  max-width: 1000px;
  margin: 0 auto;
  padding: 2rem;
  font-family: 'Segoe UI', 'PingFang SC', 'Microsoft YaHei', Arial, sans-serif;
}

.page-header {
  margin-bottom: 2rem;
}

.back-btn {
  display: inline-block;
  color: #55a3ff;
  text-decoration: none;
  margin-bottom: 1rem;
  font-weight: 500;
}

.back-btn:hover {
  color: #1e3799;
}

.page-header h1 {
  color: #2c3e50;
  margin: 0 0 0.5rem 0;
}

.page-header p {
  color: #7f8c8d;
  margin: 0;
}

.realtime-voice-chat {
  background: white;
  border-radius: 16px;
  padding: 2rem;
  box-shadow: 0 4px 24px 0 #e0e7ef44;
}

.controls {
  display: flex;
  align-items: center;
  margin-bottom: 1em;
  flex-wrap: wrap;
  gap: 1rem;
}

.start-btn, .stop-btn, .manual-btn {
  padding: 0.5em 1.5em;
  border: none;
  border-radius: 6px;
  font-size: 1.1em;
  cursor: pointer;
  transition: background 0.2s;
}

.start-btn {
  background: linear-gradient(90deg, #4f8cff, #6ed0ff);
  color: #fff;
}

.stop-btn {
  background: #ff4f4f;
  color: #fff;
}

.manual-btn {
  background: #ffa500;
  color: #fff;
  font-size: 0.9em;
}

.start-btn:disabled, .stop-btn:disabled, .manual-btn:disabled {
  background: #ccc;
  color: #fff;
  cursor: not-allowed;
}

.recording-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: #ff4f4f;
  margin-left: 8px;
  animation: blink 1s infinite;
  display: inline-block;
}

@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.2; }
}

.status-indicators {
  margin-bottom: 1em;
}

.vad-indicator {
  margin: 0.5em 0;
  text-align: center;
  font-size: 1.1em;
}

.vad-on {
  color: #1a7f37;
  font-weight: bold;
}

.vad-off {
  color: #aaa;
}

.processing-status {
  display: flex;
  justify-content: center;
  gap: 1em;
  margin: 0.5em 0;
}

.status-item {
  font-size: 0.9em;
  color: #666;
  background: #f0f0f0;
  padding: 0.2em 0.6em;
  border-radius: 12px;
  animation: pulse 1.5s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 0.7; }
  50% { opacity: 1; }
}

.chat-history {
  max-height: 400px;
  overflow-y: auto;
  background: #f6f8fa;
  border-radius: 8px;
  padding: 1em;
  margin-bottom: 1em;
  min-height: 80px;
}

.msg-bubble {
  display: flex;
  align-items: flex-start;
  margin-bottom: 0.7em;
  font-size: 1em;
}

.msg-bubble.user .msg-text {
  background: #e6f0ff;
  color: #2a4d8f;
  align-self: flex-end;
}

.msg-bubble.asr .msg-text {
  background: #fffbe6;
  color: #b59a00;
}

.msg-bubble.bot .msg-text {
  background: #e8ffe6;
  color: #1a7f37;
}

.msg-bubble.bot.playing .msg-text {
  border: 2px solid #1a7f37;
  background: #d2ffe0;
}

.msg-bubble.system .msg-text {
  background: #f0f0f0;
  color: #666;
  font-size: 0.85em;
}

.msg-text {
  display: inline-block;
  padding: 0.5em 1em;
  border-radius: 16px;
  margin-left: 0.5em;
  max-width: 80%;
  word-break: break-all;
}

.audio-status {
  margin-top: 1em;
  text-align: center;
  font-size: 0.9em;
  color: #666;
}

.playing-indicator {
  color: #1a7f37;
  font-weight: bold;
}

.queue-indicator {
  color: #b59a00;
}

.error-message {
  margin-top: 1em;
  padding: 0.8em;
  background: #ffe6e6;
  border: 1px solid #ffcccc;
  border-radius: 8px;
  color: #cc0000;
  font-size: 0.9em;
  text-align: center;
}

@media (max-width: 600px) {
  .realtime-chat {
    padding: 1rem;
  }
  
  .realtime-voice-chat {
    padding: 1em 0.5em;
  }
  
  .chat-history {
    padding: 0.5em;
    max-height: 300px;
  }
  
  .controls {
    justify-content: center;
  }
  
  .manual-btn {
    order: 3;
    width: 100%;
    margin-top: 0.5rem;
  }
}</style> 