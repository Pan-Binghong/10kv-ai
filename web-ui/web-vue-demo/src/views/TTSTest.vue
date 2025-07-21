<template>
  <div class="tts-test">
    <div class="page-header">
      <router-link to="/" class="back-btn">← 返回首页</router-link>
      <h1>🎵 TTS语音合成API测试</h1>
      <p>输入文字，生成自然语音音频</p>
    </div>

    <div class="test-container">
      <div class="input-section">
        <h3>文本输入</h3>
        <div class="text-input-area">
          <textarea 
            v-model="inputText" 
            :disabled="isGenerating"
            placeholder="输入要合成语音的文字... (建议50-200字，避免过长文本)"
            class="text-input"
            rows="6"
            maxlength="500"
          ></textarea>
          <div class="input-info">
            <span class="char-count">{{ inputText.length }}/500 字符</span>
            <span class="word-estimate">约 {{ estimatedDuration }} 秒音频</span>
          </div>
        </div>
        
        <div class="quick-texts">
          <h4>快速测试文本</h4>
          <div class="quick-text-buttons">
            <button v-for="(sample, index) in sampleTexts" :key="index"
                    @click="selectSampleText(sample)"
                    :disabled="isGenerating"
                    class="sample-btn">
              {{ sample.name }}
            </button>
          </div>
        </div>

        <div class="control-buttons">
          <button @click="generateSpeech" 
                  :disabled="!inputText.trim() || isGenerating"
                  class="generate-btn">
            {{ isGenerating ? '生成中...' : '生成语音' }}
          </button>
          <button @click="clearText" 
                  :disabled="isGenerating"
                  class="clear-text-btn">
            清空文本
          </button>
        </div>
      </div>

      <div class="result-section">
        <h3>生成结果</h3>
        <div class="audio-result-area">
          <div v-if="isGenerating" class="generating">
            <div class="spinner"></div>
            <p>正在生成语音，请稍候...</p>
            <div class="progress-info">
              <p>⏱️ 预计需要 {{ Math.ceil(estimatedDuration * 0.3) }} 秒</p>
            </div>
          </div>
          
          <div v-else-if="audioUrl" class="audio-controls">
            <div class="audio-player">
              <audio ref="audioRef" :src="audioUrl" controls preload="metadata"
                     @loadedmetadata="onAudioLoaded"
                     @play="isPlaying = true"
                     @pause="isPlaying = false"
                     @ended="isPlaying = false">
                您的浏览器不支持音频播放
              </audio>
            </div>
            
            <div class="audio-info" v-if="audioInfo.duration">
              <div class="info-item">
                <strong>时长:</strong> {{ formatDuration(audioInfo.duration) }}
              </div>
              <div class="info-item">
                <strong>文件大小:</strong> {{ audioInfo.size }}
              </div>
              <div class="info-item">
                <strong>生成文本:</strong> {{ generatedText }}
              </div>
            </div>
            
            <div class="audio-actions">
              <button @click="downloadAudio" class="download-btn">
                📥 下载音频
              </button>
              <button @click="playPause" 
                      :class="['play-btn', { playing: isPlaying }]">
                {{ isPlaying ? '⏸️ 暂停' : '▶️ 播放' }}
              </button>
              <button @click="clearAudio" class="clear-audio-btn">
                🗑️ 清除音频
              </button>
            </div>
          </div>
          
          <div v-else-if="error" class="error-result">
            <div class="error-icon">⚠️</div>
            <p>{{ error }}</p>
            <button @click="clearError" class="retry-btn">重试</button>
          </div>
          
          <div v-else class="empty-result">
            <div class="empty-icon">🎵</div>
            <p>生成的语音将在这里播放</p>
          </div>
        </div>
      </div>

      <div class="settings-section">
        <h3>合成设置</h3>
        <div class="settings-grid">
          <div class="setting-item">
            <label>模型:</label>
            <select v-model="settings.model" :disabled="isGenerating">
              <option value="CosyVoice2-0.5B">CosyVoice2-0.5B (推荐)</option>
              <option value="ChatTTS">ChatTTS</option>
            </select>
          </div>
          <div class="setting-item">
            <label>语音类型:</label>
            <select v-model="settings.voice" :disabled="isGenerating">
              <option value="中文女声">中文女声</option>
              <option value="中文男声">中文男声</option>
              <option value="英文女声">英文女声</option>
              <option value="英文男声">英文男声</option>
            </select>
          </div>
          <div class="setting-item">
            <label>语音质量:</label>
            <select v-model="settings.quality" :disabled="isGenerating">
              <option value="high">高质量 (较慢)</option>
              <option value="medium">中等质量 (平衡)</option>
              <option value="fast">快速生成 (较快)</option>
            </select>
          </div>
          <div class="setting-item">
            <label>输出格式:</label>
            <select v-model="settings.format" :disabled="isGenerating">
              <option value="wav">WAV (无损)</option>
              <option value="mp3">MP3 (压缩)</option>
            </select>
          </div>
        </div>
      </div>

      <div class="api-info">
        <h3>API信息</h3>
        <div class="info-grid">
          <div class="info-item">
            <strong>接口地址:</strong>
            <code>POST /v1/audio/speech</code>
          </div>
          <div class="info-item">
            <strong>当前模型:</strong>
            <span>{{ settings.model }}</span>
          </div>
          <div class="info-item">
            <strong>当前语音:</strong>
            <span>{{ settings.voice }}</span>
          </div>
          <div class="info-item">
            <strong>支持格式:</strong>
            <span>WAV, MP3</span>
          </div>
          <div class="info-item">
            <strong>字符限制:</strong>
            <span>500字符以内</span>
          </div>
          <div class="info-item">
            <strong>语音类型:</strong>
            <span>中英文男女声</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const inputText = ref('')
const isGenerating = ref(false)
const isPlaying = ref(false)
const audioUrl = ref('')
const generatedText = ref('')
const error = ref('')
const audioRef = ref(null)

const audioInfo = ref({
  duration: 0,
  size: ''
})

const settings = ref({
  model: 'CosyVoice2-0.5B',
  voice: '中文女声',
  quality: 'medium',
  format: 'wav'
})

const API_BASE_URL = 'http://127.0.0.1:8000/api/v1'

const sampleTexts = [
  {
    name: '问候语',
    text: '你好！欢迎使用语音合成系统，我是你的AI助手。'
  },
  {
    name: '天气播报',
    text: '今天天气晴朗，气温适宜，是出门游玩的好日子。请注意防晒和补水。'
  },
  {
    name: '新闻播报',
    text: '人工智能技术在各个领域的应用日益广泛，为人类生活带来了诸多便利。'
  },
  {
    name: '诗歌朗诵',
    text: '明月几时有？把酒问青天。不知天上宫阙，今夕是何年。'
  },
  {
    name: '技术介绍',
    text: 'CosyVoice2是一款先进的文本转语音模型，能够生成自然流畅的多语言语音。'
  },
  {
    name: '英文测试',
    text: 'Hello, this is a test of CosyVoice2 English synthesis capability.'
  }
]

const estimatedDuration = computed(() => {
  // 估算音频时长：中文约2.5字/秒
  return Math.ceil(inputText.value.length / 2.5)
})

function selectSampleText(sample) {
  inputText.value = sample.text
  clearResults()
}

function clearText() {
  inputText.value = ''
  clearResults()
}

function clearResults() {
  clearAudio()
  clearError()
}

function clearAudio() {
  if (audioUrl.value) {
    URL.revokeObjectURL(audioUrl.value)
    audioUrl.value = ''
  }
  generatedText.value = ''
  audioInfo.value = { duration: 0, size: '' }
  isPlaying.value = false
}

function clearError() {
  error.value = ''
}

function formatFileSize(bytes) {
  if (bytes === 0) return '0 Bytes'
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

function formatDuration(seconds) {
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins}:${secs.toString().padStart(2, '0')}`
}

async function generateSpeech() {
  if (!inputText.value.trim()) return

  isGenerating.value = true
  clearResults()
  
  const textToGenerate = inputText.value.trim()
  generatedText.value = textToGenerate

  try {
    const payload = {
      model: settings.value.model,
      input: textToGenerate,
      voice: settings.value.voice,
      response_format: settings.value.format,
      speed: settings.value.quality === 'fast' ? 1.2 : settings.value.quality === 'high' ? 0.8 : 1.0
    }

    const response = await fetch(`${API_BASE_URL}/audio/speech`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(payload)
    })

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`)
    }

    const audioBlob = await response.blob()
    const url = URL.createObjectURL(audioBlob)
    audioUrl.value = url
    
    // 设置音频信息
    audioInfo.value.size = formatFileSize(audioBlob.size)

  } catch (err) {
    console.error('TTS生成失败:', err)
    error.value = `语音生成失败: ${err.message}`
  } finally {
    isGenerating.value = false
  }
}

function onAudioLoaded() {
  if (audioRef.value) {
    audioInfo.value.duration = audioRef.value.duration
  }
}

function playPause() {
  if (!audioRef.value) return
  
  if (isPlaying.value) {
    audioRef.value.pause()
  } else {
    audioRef.value.play()
  }
}

function downloadAudio() {
  if (!audioUrl.value) return
  
  const link = document.createElement('a')
  link.href = audioUrl.value
  link.download = `tts_audio_${Date.now()}.${settings.value.format}`
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
}
</script>

<style scoped>
.tts-test {
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
  color: #fdcb6e;
  text-decoration: none;
  margin-bottom: 1rem;
  font-weight: 500;
}

.back-btn:hover {
  color: #e17055;
}

.page-header h1 {
  color: #2c3e50;
  margin: 0 0 0.5rem 0;
}

.page-header p {
  color: #7f8c8d;
  margin: 0;
}

.test-container {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 2rem;
}

.input-section, .result-section {
  background: white;
  border-radius: 12px;
  padding: 2rem;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
}

.input-section h3, .result-section h3 {
  color: #2c3e50;
  margin: 0 0 1rem 0;
}

.text-input-area {
  margin-bottom: 2rem;
}

.text-input {
  width: 100%;
  border: 1px solid #e1e8ed;
  border-radius: 8px;
  padding: 1rem;
  font-family: inherit;
  font-size: 0.95rem;
  line-height: 1.5;
  resize: vertical;
  box-sizing: border-box;
}

.text-input:focus {
  outline: none;
  border-color: #fdcb6e;
}

.text-input:disabled {
  background: #f8f9fa;
  cursor: not-allowed;
}

.input-info {
  display: flex;
  justify-content: space-between;
  margin-top: 0.5rem;
  font-size: 0.9rem;
  color: #7f8c8d;
}

.char-count {
  color: #95a5a6;
}

.word-estimate {
  color: #fdcb6e;
  font-weight: 500;
}

.quick-texts {
  margin-bottom: 2rem;
}

.quick-texts h4 {
  color: #2c3e50;
  margin: 0 0 1rem 0;
  font-size: 1rem;
}

.quick-text-buttons {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.sample-btn {
  background: #f8f9fa;
  border: 1px solid #e1e8ed;
  color: #2c3e50;
  padding: 0.5rem 1rem;
  border-radius: 20px;
  cursor: pointer;
  font-size: 0.9rem;
  transition: all 0.2s;
}

.sample-btn:hover:not(:disabled) {
  background: #fdcb6e;
  color: white;
  border-color: #fdcb6e;
}

.sample-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.control-buttons {
  display: flex;
  gap: 1rem;
}

.generate-btn {
  background: #fdcb6e;
  color: white;
  border: none;
  padding: 0.8rem 2rem;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 500;
  font-size: 1rem;
  transition: background 0.2s;
}

.generate-btn:hover:not(:disabled) {
  background: #e17055;
}

.generate-btn:disabled {
  background: #bdc3c7;
  cursor: not-allowed;
}

.clear-text-btn {
  background: #e17055;
  color: white;
  border: none;
  padding: 0.8rem 1.5rem;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 500;
}

.audio-result-area {
  min-height: 200px;
  border: 1px solid #e1e8ed;
  border-radius: 8px;
  padding: 1rem;
  background: #f8f9fa;
}

.generating {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 180px;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #e1e8ed;
  border-top: 4px solid #fdcb6e;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 1rem;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.progress-info {
  margin-top: 1rem;
  text-align: center;
  color: #7f8c8d;
  font-size: 0.9rem;
}

.audio-controls {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.audio-player {
  display: flex;
  justify-content: center;
}

.audio-player audio {
  width: 100%;
  max-width: 400px;
}

.audio-info {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 1rem;
  padding: 1rem;
  background: white;
  border-radius: 6px;
  border: 1px solid #e1e8ed;
}

.audio-info .info-item {
  font-size: 0.9rem;
}

.audio-info .info-item strong {
  display: block;
  color: #2c3e50;
  margin-bottom: 0.2rem;
}

.audio-actions {
  display: flex;
  gap: 0.5rem;
  justify-content: center;
  flex-wrap: wrap;
}

.download-btn, .play-btn, .clear-audio-btn {
  background: #74b9ff;
  color: white;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.9rem;
  transition: background 0.2s;
}

.play-btn.playing {
  background: #e74c3c;
}

.clear-audio-btn {
  background: #e17055;
}

.download-btn:hover {
  background: #0984e3;
}

.play-btn:hover {
  background: #e84393;
}

.clear-audio-btn:hover {
  background: #c0392b;
}

.error-result {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 180px;
  color: #e74c3c;
}

.error-icon {
  font-size: 2rem;
  margin-bottom: 1rem;
}

.retry-btn {
  background: #e74c3c;
  color: white;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 6px;
  cursor: pointer;
  margin-top: 1rem;
}

.empty-result {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 180px;
  color: #95a5a6;
}

.empty-icon {
  font-size: 2rem;
  margin-bottom: 1rem;
}

.settings-section, .api-info {
  background: white;
  border-radius: 12px;
  padding: 1.5rem;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
  height: fit-content;
}

.settings-section h3, .api-info h3 {
  color: #2c3e50;
  margin: 0 0 1rem 0;
  font-size: 1.1rem;
}

.settings-grid {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.setting-item {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.setting-item label {
  font-weight: 500;
  color: #2c3e50;
  font-size: 0.9rem;
}

.setting-item select {
  padding: 0.5rem;
  border: 1px solid #e1e8ed;
  border-radius: 6px;
  font-size: 0.9rem;
}

.info-grid {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.info-grid .info-item {
  padding: 0.8rem;
  background: #f8f9fa;
  border-radius: 6px;
  font-size: 0.9rem;
}

.info-grid .info-item strong {
  display: block;
  color: #2c3e50;
  margin-bottom: 0.3rem;
}

.info-grid .info-item code {
  background: #e1e8ed;
  padding: 0.2rem 0.4rem;
  border-radius: 3px;
  font-family: 'Courier New', monospace;
}

@media (max-width: 768px) {
  .tts-test {
    padding: 1rem;
  }
  
  .test-container {
    grid-template-columns: 1fr;
    gap: 1rem;
  }
  
  .control-buttons {
    flex-direction: column;
  }
  
  .quick-text-buttons {
    flex-direction: column;
  }
  
  .audio-actions {
    flex-direction: column;
  }
  
  .audio-info {
    grid-template-columns: 1fr;
  }
}</style> 