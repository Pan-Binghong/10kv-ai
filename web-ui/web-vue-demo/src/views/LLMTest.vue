<template>
  <div class="llm-test">
    <div class="page-header">
      <router-link to="/" class="back-btn">← 返回首页</router-link>
      <h1>🧠 LLM对话API测试</h1>
      <p>测试大语言模型对话功能，支持流式响应</p>
    </div>

    <div class="test-container">
      <div class="chat-section">
        <div class="chat-history" ref="chatHistoryRef">
          <div v-if="messages.length === 0" class="empty-chat">
            <div class="empty-icon">💬</div>
            <p>开始你的对话吧！</p>
          </div>
          <div v-for="(message, index) in messages" :key="index" 
               :class="['message', message.role]">
            <div class="message-content">
              <div class="message-role">
                {{ message.role === 'user' ? '👤 用户' : '🤖 助手' }}
              </div>
              <div class="message-text" v-html="formatMessage(message.content)"></div>
              <div class="message-time">{{ message.timestamp }}</div>
            </div>
          </div>
          <div v-if="isStreaming" class="message assistant streaming">
            <div class="message-content">
              <div class="message-role">🤖 助手</div>
              <div class="message-text">
                {{ streamingContent }}
                <span class="cursor">|</span>
              </div>
            </div>
          </div>
        </div>
        
        <div class="input-section">
          <div class="input-container">
            <textarea 
              v-model="inputMessage" 
              @keydown.enter.prevent="handleEnterKey"
              :disabled="isStreaming"
              placeholder="输入你的问题... (Shift+Enter换行，Enter发送)"
              class="message-input"
              rows="3"
            ></textarea>
            <button @click="sendMessage" :disabled="!inputMessage.trim() || isStreaming" 
                    class="send-btn">
              {{ isStreaming ? '生成中...' : '发送' }}
            </button>
          </div>
          <div class="input-controls">
            <button @click="clearChat" :disabled="isStreaming" class="clear-btn">
              清除对话
            </button>
            <button @click="stopGeneration" v-if="isStreaming" class="stop-btn">
              停止生成
            </button>
          </div>
        </div>
      </div>

      <div class="settings-section">
        <h3>对话设置</h3>
        <div class="settings-grid">
          <div class="setting-item">
            <label>模型:</label>
            <select v-model="settings.model">
              <option value="gpt-4o-ca">GPT-4O</option>
              <option value="gpt-3.5-turbo">GPT-3.5-Turbo</option>
            </select>
          </div>
          <div class="setting-item">
            <label>温度 ({{ settings.temperature }}):</label>
            <input type="range" v-model.number="settings.temperature" 
                   min="0" max="2" step="0.1" class="slider">
          </div>
          <div class="setting-item">
            <label>最大长度:</label>
            <input type="number" v-model.number="settings.maxTokens" 
                   min="100" max="4000" step="100" class="number-input">
          </div>
          <div class="setting-item">
            <label>流式响应:</label>
            <input type="checkbox" v-model="settings.stream" class="checkbox">
          </div>
        </div>
      </div>

      <div class="api-info">
        <h3>API信息</h3>
        <div class="info-content">
          <div class="info-item">
            <strong>接口地址:</strong>
            <code>POST /v1/chat/completions</code>
          </div>
          <div class="info-item">
            <strong>当前模型:</strong>
            <span>{{ settings.model }}</span>
          </div>
          <div class="info-item">
            <strong>响应方式:</strong>
            <span>{{ settings.stream ? '流式响应' : '一次性响应' }}</span>
          </div>
          <div class="info-item">
            <strong>消息计数:</strong>
            <span>{{ messages.length }} 条</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick, watch } from 'vue'

const messages = ref([])
const inputMessage = ref('')
const isStreaming = ref(false)
const streamingContent = ref('')
const chatHistoryRef = ref(null)
const abortController = ref(null)

const settings = ref({
  model: 'gpt-4o-ca',
  temperature: 0.7,
  maxTokens: 1000,
  stream: true
})

const API_BASE_URL = 'http://127.0.0.1:8000/api/v1'

function formatMessage(content) {
  // 简单的markdown格式化
  return content
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/`(.*?)`/g, '<code>$1</code>')
    .replace(/\n/g, '<br>')
}

function getCurrentTime() {
  return new Date().toLocaleTimeString('zh-CN', { 
    hour12: false, 
    hour: '2-digit', 
    minute: '2-digit' 
  })
}

async function scrollToBottom() {
  await nextTick()
  if (chatHistoryRef.value) {
    chatHistoryRef.value.scrollTop = chatHistoryRef.value.scrollHeight
  }
}

function handleEnterKey(event) {
  if (event.shiftKey) {
    // Shift+Enter 允许换行
    return
  }
  // Enter 发送消息
  sendMessage()
}

async function sendMessage() {
  if (!inputMessage.value.trim() || isStreaming.value) return

  const userMessage = {
    role: 'user',
    content: inputMessage.value.trim(),
    timestamp: getCurrentTime()
  }

  messages.value.push(userMessage)
  const currentInput = inputMessage.value.trim()
  inputMessage.value = ''
  await scrollToBottom()

  // 开始流式响应
  isStreaming.value = true
  streamingContent.value = ''
  abortController.value = new AbortController()

  try {
    const payload = {
      model: settings.value.model,
      messages: messages.value.map(msg => ({
        role: msg.role,
        content: msg.content
      })),
      stream: settings.value.stream,
      max_tokens: settings.value.maxTokens,
      temperature: settings.value.temperature
    }

    const response = await fetch(`${API_BASE_URL}/chat/completions`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer your-api-key' // 这里需要配置实际的API密钥
      },
      body: JSON.stringify(payload),
      signal: abortController.value.signal
    })

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`)
    }

    if (settings.value.stream) {
      await handleStreamResponse(response)
    } else {
      await handleNormalResponse(response)
    }

  } catch (error) {
    if (error.name === 'AbortError') {
      console.log('请求被取消')
    } else {
      console.error('LLM请求失败:', error)
      messages.value.push({
        role: 'assistant',
        content: `❌ 请求失败: ${error.message}`,
        timestamp: getCurrentTime()
      })
    }
  } finally {
    isStreaming.value = false
    streamingContent.value = ''
    await scrollToBottom()
  }
}

async function handleStreamResponse(response) {
  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let fullContent = ''

  try {
    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      const chunk = decoder.decode(value)
      const lines = chunk.split('\n')

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = line.slice(6).trim()
          if (data === '[DONE]') {
            break
          }
          
          try {
            const parsed = JSON.parse(data)
            const delta = parsed.choices?.[0]?.delta?.content
            if (delta) {
              fullContent += delta
              streamingContent.value = fullContent
              await scrollToBottom()
            }
          } catch (e) {
            // 忽略解析错误
          }
        }
      }
    }
  } finally {
    if (fullContent) {
      messages.value.push({
        role: 'assistant',
        content: fullContent,
        timestamp: getCurrentTime()
      })
    }
  }
}

async function handleNormalResponse(response) {
  const result = await response.json()
  const content = result.choices?.[0]?.message?.content || '无响应内容'
  
  messages.value.push({
    role: 'assistant',
    content: content,
    timestamp: getCurrentTime()
  })
}

function stopGeneration() {
  if (abortController.value) {
    abortController.value.abort()
  }
}

function clearChat() {
  messages.value = []
  streamingContent.value = ''
}

// 监听流式内容变化，自动滚动
watch(streamingContent, scrollToBottom)
</script>

<style scoped>
.llm-test {
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
  color: #fd79a8;
  text-decoration: none;
  margin-bottom: 1rem;
  font-weight: 500;
}

.back-btn:hover {
  color: #e84393;
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

.chat-section {
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
  display: flex;
  flex-direction: column;
  height: 600px;
}

.chat-history {
  flex: 1;
  overflow-y: auto;
  padding: 1rem;
  background: #f8f9fa;
}

.empty-chat {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #95a5a6;
}

.empty-icon {
  font-size: 3rem;
  margin-bottom: 1rem;
}

.message {
  margin-bottom: 1rem;
  display: flex;
}

.message.user {
  justify-content: flex-end;
}

.message.assistant {
  justify-content: flex-start;
}

.message-content {
  max-width: 80%;
  padding: 1rem;
  border-radius: 12px;
  position: relative;
}

.message.user .message-content {
  background: #fd79a8;
  color: white;
}

.message.assistant .message-content {
  background: white;
  border: 1px solid #e1e8ed;
}

.message.streaming .message-content {
  border-color: #fd79a8;
}

.message-role {
  font-size: 0.8rem;
  font-weight: bold;
  margin-bottom: 0.5rem;
  opacity: 0.8;
}

.message-text {
  line-height: 1.5;
  word-wrap: break-word;
}

.message-text code {
  background: rgba(0, 0, 0, 0.1);
  padding: 0.2rem 0.4rem;
  border-radius: 3px;
  font-family: 'Courier New', monospace;
  font-size: 0.9rem;
}

.cursor {
  animation: blink 1s infinite;
}

@keyframes blink {
  0%, 50% { opacity: 1; }
  51%, 100% { opacity: 0; }
}

.message-time {
  font-size: 0.7rem;
  opacity: 0.6;
  margin-top: 0.5rem;
}

.input-section {
  border-top: 1px solid #e1e8ed;
  padding: 1rem;
}

.input-container {
  display: flex;
  gap: 1rem;
  margin-bottom: 1rem;
}

.message-input {
  flex: 1;
  border: 1px solid #e1e8ed;
  border-radius: 8px;
  padding: 0.8rem;
  resize: vertical;
  font-family: inherit;
  font-size: 0.9rem;
}

.message-input:focus {
  outline: none;
  border-color: #fd79a8;
}

.message-input:disabled {
  background: #f8f9fa;
  cursor: not-allowed;
}

.send-btn {
  background: #fd79a8;
  color: white;
  border: none;
  padding: 0.8rem 1.5rem;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 500;
  white-space: nowrap;
}

.send-btn:hover:not(:disabled) {
  background: #e84393;
}

.send-btn:disabled {
  background: #bdc3c7;
  cursor: not-allowed;
}

.input-controls {
  display: flex;
  gap: 1rem;
}

.clear-btn, .stop-btn {
  background: #e17055;
  color: white;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.9rem;
}

.stop-btn {
  background: #e74c3c;
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

.setting-item select, .number-input {
  padding: 0.5rem;
  border: 1px solid #e1e8ed;
  border-radius: 6px;
  font-size: 0.9rem;
}

.slider {
  -webkit-appearance: none;
  height: 4px;
  border-radius: 2px;
  background: #e1e8ed;
  outline: none;
}

.slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: #fd79a8;
  cursor: pointer;
}

.checkbox {
  width: 20px;
  height: 20px;
}

.info-content {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.info-item {
  padding: 0.8rem;
  background: #f8f9fa;
  border-radius: 6px;
  font-size: 0.9rem;
}

.info-item strong {
  display: block;
  color: #2c3e50;
  margin-bottom: 0.3rem;
}

.info-item code {
  background: #e1e8ed;
  padding: 0.2rem 0.4rem;
  border-radius: 3px;
  font-family: 'Courier New', monospace;
}

@media (max-width: 768px) {
  .llm-test {
    padding: 1rem;
  }
  
  .test-container {
    grid-template-columns: 1fr;
    gap: 1rem;
  }
  
  .chat-section {
    height: 500px;
  }
  
  .input-container {
    flex-direction: column;
  }
  
  .input-controls {
    flex-direction: column;
  }
  
  .message-content {
    max-width: 95%;
  }
}</style> 