<template>
  <div class="transcribe-test">
    <div class="page-header">
      <router-link to="/" class="back-btn">← 返回首页</router-link>
      <div class="header-content">
        <h1>📝 语音转录API测试</h1>
        <p>上传音频文件，测试语音转文字功能</p>
      </div>
    </div>

    <div class="test-container">
      <div class="upload-section">
        <div class="section-header">
          <h3>📁 音频文件上传</h3>
        </div>
        <div class="upload-area" :class="{ dragover: isDragOver, uploading: isUploading }" 
             @dragover.prevent="isDragOver = true"
             @dragleave.prevent="isDragOver = false"
             @drop.prevent="handleFileDrop">
          <div v-if="!selectedFile" class="upload-placeholder">
            <div class="upload-icon">🎵</div>
            <h3>拖拽音频文件到这里</h3>
            <p>或者点击下方按钮选择文件</p>
            <p class="file-hint">支持格式: WAV, MP3, M4A (推荐WAV, 16kHz)</p>
          </div>
          <div v-else class="file-info">
            <div class="file-icon">🎼</div>
            <h3>{{ selectedFile.name }}</h3>
            <p>大小: {{ formatFileSize(selectedFile.size) }}</p>
            <button @click="clearFile" class="clear-btn">清除</button>
          </div>
        </div>
        
        <div class="upload-controls">
          <label for="file-input" class="file-input-label">
            <input type="file" id="file-input" @change="handleFileSelect" 
                   accept="audio/*" style="display: none;">
            📁 选择音频文件
          </label>
          <button @click="transcribeAudio" :disabled="!selectedFile || isUploading" 
                  class="transcribe-btn">
            <span v-if="isUploading">⏳ 转录中...</span>
            <span v-else>🚀 开始转录</span>
          </button>
        </div>
      </div>

      <div class="result-section">
        <div class="section-header">
          <h3>📄 转录结果</h3>
        </div>
        <div class="result-area">
          <div v-if="isUploading" class="loading">
            <div class="spinner"></div>
            <p>🎯 正在处理音频，请稍候...</p>
            <div class="progress-bar">
              <div class="progress-fill"></div>
            </div>
          </div>
          <div v-else-if="transcriptionResult" class="result-content">
            <div class="result-text">{{ transcriptionResult }}</div>
            <div class="result-meta">
              <span class="word-count">字数: {{ transcriptionResult.length }}</span>
              <span class="timestamp">转录时间: {{ new Date().toLocaleTimeString() }}</span>
            </div>
            <div class="result-actions">
              <button @click="copyResult" class="copy-btn">📋 复制文本</button>
              <button @click="clearResult" class="clear-result-btn">🗑️ 清除结果</button>
            </div>
          </div>
          <div v-else-if="error" class="error-content">
            <div class="error-icon">⚠️</div>
            <p>{{ error }}</p>
            <button @click="clearResults" class="retry-btn">🔄 重试</button>
          </div>
          <div v-else class="empty-result">
            <div class="empty-icon">📝</div>
            <p>转录结果将在这里显示</p>
            <span class="empty-hint">上传音频文件开始转录</span>
          </div>
        </div>
      </div>

      <div class="api-info">
        <div class="section-header">
          <h3>⚙️ API信息</h3>
        </div>
        <div class="info-grid">
          <div class="info-item">
            <strong>🔗 接口地址:</strong>
            <code>POST /v1/audio/transcriptions</code>
          </div>
          <div class="info-item">
            <strong>🤖 模型:</strong>
            <span class="model-badge">SenseVoiceSmall</span>
          </div>
          <div class="info-item">
            <strong>📁 支持格式:</strong>
            <span>WAV, MP3, M4A</span>
          </div>
          <div class="info-item">
            <strong>⚡ 推荐设置:</strong>
            <span>16kHz采样率，单声道</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const selectedFile = ref(null)
const isDragOver = ref(false)
const isUploading = ref(false)
const transcriptionResult = ref('')
const error = ref('')

const API_BASE_URL = 'http://127.0.0.1:8000/api/v1'

function handleFileSelect(event) {
  const file = event.target.files[0]
  if (file) {
    selectedFile.value = file
    clearResults()
  }
}

function handleFileDrop(event) {
  isDragOver.value = false
  const files = event.dataTransfer.files
  if (files.length > 0) {
    selectedFile.value = files[0]
    clearResults()
  }
}

function clearFile() {
  selectedFile.value = null
  clearResults()
}

function clearResult() {
  transcriptionResult.value = ''
}

function clearResults() {
  transcriptionResult.value = ''
  error.value = ''
}

function formatFileSize(bytes) {
  if (bytes === 0) return '0 Bytes'
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

async function transcribeAudio() {
  if (!selectedFile.value) return

  isUploading.value = true
  clearResults()

  try {
    const formData = new FormData()
    formData.append('file', selectedFile.value)
    formData.append('model', 'SenseVoiceSmall')

    const response = await fetch(`${API_BASE_URL}/audio/transcriptions`, {
      method: 'POST',
      body: formData
    })

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`)
    }

    const result = await response.json()
    transcriptionResult.value = result.text || '转录结果为空'
    
  } catch (err) {
    console.error('转录失败:', err)
    error.value = `转录失败: ${err.message}`
  } finally {
    isUploading.value = false
  }
}

async function copyResult() {
  try {
    await navigator.clipboard.writeText(transcriptionResult.value)
    // 简单的复制反馈
    const btn = event.target
    const originalText = btn.textContent
    btn.textContent = '已复制!'
    setTimeout(() => {
      btn.textContent = originalText
    }, 1000)
  } catch (err) {
    console.error('复制失败:', err)
  }
}
</script>

<style scoped>
.transcribe-test {
  min-height: 100vh;
  max-width: none;
  width: 100%;
  margin: 0;
  padding: 1rem;
  font-family: 'Segoe UI', 'PingFang SC', 'Microsoft YaHei', Arial, sans-serif;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.page-header {
  margin-bottom: 2rem;
  text-align: center;
  color: white;
}

.back-btn {
  display: inline-block;
  color: #ffffff;
  background: rgba(255, 255, 255, 0.2);
  text-decoration: none;
  margin-bottom: 1rem;
  font-weight: 500;
  padding: 0.5rem 1rem;
  border-radius: 20px;
  backdrop-filter: blur(10px);
  transition: all 0.3s ease;
}

.back-btn:hover {
  background: rgba(255, 255, 255, 0.3);
  transform: translateY(-2px);
}

.header-content {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.page-header h1 {
  color: white;
  margin: 0 0 0.5rem 0;
  font-size: 2.5rem;
  text-shadow: 0 2px 10px rgba(0, 0, 0, 0.3);
}

.page-header p {
  color: rgba(255, 255, 255, 0.9);
  margin: 0;
  font-size: 1.1rem;
}

.test-container {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 2rem;
  max-width: 1400px;
  margin: 0 auto;
}

.upload-section, .result-section {
  background: rgba(255, 255, 255, 0.95);
  border-radius: 20px;
  padding: 2.5rem;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  transition: all 0.3s ease;
}

.upload-section:hover, .result-section:hover {
  transform: translateY(-5px);
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.15);
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
  padding-bottom: 1rem;
  border-bottom: 2px solid #f0f0f0;
}

.section-header h3 {
  color: #2c3e50;
  margin: 0;
  font-size: 1.4rem;
  font-weight: 600;
}

.upload-area {
  border: 3px dashed #bdc3c7;
  border-radius: 16px;
  padding: 4rem 2rem;
  text-align: center;
  transition: all 0.3s ease;
  margin-bottom: 2rem;
  background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
  min-height: 200px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
}

.upload-area.dragover {
  border-color: #74b9ff;
  background: linear-gradient(135deg, #f8fbff 0%, #e3f2fd 100%);
  transform: scale(1.02);
}

.upload-area.uploading {
  border-color: #fdcb6e;
  background: linear-gradient(135deg, #fffdf8 0%, #fff9e6 100%);
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0% { transform: scale(1); }
  50% { transform: scale(1.01); }
  100% { transform: scale(1); }
}

.upload-placeholder .upload-icon,
.file-info .file-icon {
  font-size: 4rem;
  margin-bottom: 1.5rem;
}

.upload-placeholder h3,
.file-info h3 {
  color: #2c3e50;
  margin: 0 0 1rem 0;
  font-size: 1.3rem;
}

.upload-placeholder p,
.file-info p {
  color: #7f8c8d;
  margin: 0.5rem 0;
  font-size: 1rem;
}

.file-hint {
  font-size: 0.95rem;
  color: #95a5a6 !important;
}

.clear-btn {
  background: linear-gradient(135deg, #e74c3c 0%, #c0392b 100%);
  color: white;
  border: none;
  padding: 0.8rem 1.5rem;
  border-radius: 8px;
  cursor: pointer;
  margin-top: 1.5rem;
  font-weight: 500;
  transition: all 0.3s ease;
}

.clear-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 15px rgba(231, 76, 60, 0.3);
}

.upload-controls {
  display: flex;
  gap: 1.5rem;
  justify-content: center;
  flex-wrap: wrap;
}

.file-input-label {
  background: linear-gradient(135deg, #74b9ff 0%, #0984e3 100%);
  color: white;
  padding: 1.2rem 2.5rem;
  border-radius: 12px;
  cursor: pointer;
  text-decoration: none;
  font-weight: 600;
  transition: all 0.3s ease;
  box-shadow: 0 4px 15px rgba(116, 185, 255, 0.3);
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 1rem;
}

.file-input-label:hover {
  transform: translateY(-3px);
  box-shadow: 0 6px 20px rgba(116, 185, 255, 0.4);
}

.transcribe-btn {
  background: linear-gradient(135deg, #00b894 0%, #00a085 100%);
  color: white;
  border: none;
  padding: 1.2rem 2.5rem;
  border-radius: 12px;
  cursor: pointer;
  font-weight: 600;
  transition: all 0.3s ease;
  box-shadow: 0 4px 15px rgba(0, 184, 148, 0.3);
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 1rem;
}

.transcribe-btn:hover:not(:disabled) {
  transform: translateY(-3px);
  box-shadow: 0 6px 20px rgba(0, 184, 148, 0.4);
}

.transcribe-btn:disabled {
  background: #bdc3c7;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}

.result-area {
  min-height: 250px;
  border: 2px solid #e1e8ed;
  border-radius: 16px;
  padding: 2rem;
  background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 200px;
}

.spinner {
  width: 50px;
  height: 50px;
  border: 5px solid #e1e8ed;
  border-top: 5px solid #74b9ff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 1.5rem;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.progress-bar {
  width: 100%;
  height: 12px;
  background-color: #e1e8ed;
  border-radius: 6px;
  margin-top: 1.5rem;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #00b894, #00a085);
  border-radius: 6px;
  width: 0%;
  animation: progressAnimation 3s infinite;
}

@keyframes progressAnimation {
  0% { width: 0%; }
  50% { width: 70%; }
  100% { width: 95%; }
}

.result-content {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  animation: fadeInUp 0.5s ease-out;
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.result-text {
  background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
  padding: 2rem;
  border-radius: 16px;
  border: 2px solid #e1e8ed;
  line-height: 1.8;
  min-height: 120px;
  font-size: 1.2rem;
  color: #2c3e50 !important;
  font-family: 'Segoe UI', 'PingFang SC', 'Microsoft YaHei', Arial, sans-serif;
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.08);
  transition: all 0.3s ease;
  word-wrap: break-word;
  white-space: pre-wrap;
}

.result-text:hover {
  border-color: #74b9ff;
  box-shadow: 0 8px 25px rgba(116, 185, 255, 0.15);
}

.result-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 1rem;
  color: #7f8c8d;
  margin-top: 0.5rem;
  padding: 1rem 1.5rem;
  background: #f8f9fa;
  border-radius: 12px;
  border: 1px solid #e1e8ed;
}

.word-count {
  font-weight: 600;
  color: #00b894;
}

.timestamp {
  color: #74b9ff;
  font-weight: 500;
}

.result-actions {
  display: flex;
  gap: 1.5rem;
  justify-content: center;
  flex-wrap: wrap;
}

.copy-btn {
  background: linear-gradient(135deg, #74b9ff 0%, #0984e3 100%);
  color: white;
  border: none;
  padding: 1rem 2rem;
  border-radius: 12px;
  cursor: pointer;
  font-size: 1rem;
  font-weight: 500;
  transition: all 0.3s ease;
  box-shadow: 0 4px 15px rgba(116, 185, 255, 0.3);
}

.copy-btn:hover {
  transform: translateY(-3px);
  box-shadow: 0 6px 20px rgba(116, 185, 255, 0.4);
}

.clear-result-btn {
  background: linear-gradient(135deg, #e17055 0%, #d63031 100%);
  color: white;
  border: none;
  padding: 1rem 2rem;
  border-radius: 12px;
  cursor: pointer;
  font-size: 1rem;
  font-weight: 500;
  transition: all 0.3s ease;
  box-shadow: 0 4px 15px rgba(225, 112, 85, 0.3);
}

.clear-result-btn:hover {
  transform: translateY(-3px);
  box-shadow: 0 6px 20px rgba(225, 112, 85, 0.4);
}

.retry-btn {
  background: linear-gradient(135deg, #3498db 0%, #2980b9 100%);
  color: white;
  border: none;
  padding: 1rem 2rem;
  border-radius: 12px;
  cursor: pointer;
  font-size: 1rem;
  font-weight: 500;
  transition: all 0.3s ease;
  box-shadow: 0 4px 15px rgba(52, 152, 219, 0.3);
}

.retry-btn:hover {
  transform: translateY(-3px);
  box-shadow: 0 6px 20px rgba(52, 152, 219, 0.4);
}

.error-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 200px;
  color: #e74c3c;
}

.error-icon {
  font-size: 3rem;
  margin-bottom: 1rem;
}

.empty-result {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 200px;
  color: #95a5a6;
}

.empty-icon {
  font-size: 3rem;
  margin-bottom: 1rem;
}

.empty-hint {
  font-size: 1rem;
  color: #bdc3c7;
  margin-top: 0.5rem;
}

.api-info {
  grid-column: 1 / -1;
  background: rgba(255, 255, 255, 0.95);
  border-radius: 20px;
  padding: 2.5rem;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  margin-top: 1rem;
  transition: all 0.3s ease;
}

.api-info:hover {
  transform: translateY(-5px);
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.15);
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 1.5rem;
}

.info-item {
  padding: 2rem;
  background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
  border-radius: 16px;
  transition: all 0.3s ease;
  border: 1px solid #e1e8ed;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05);
}

.info-item:hover {
  transform: translateY(-3px);
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
}

.info-item strong {
  display: block;
  color: #2c3e50;
  margin-bottom: 1rem;
  font-size: 1rem;
}

.info-item code {
  background: #e1e8ed;
  padding: 0.5rem 1rem;
  border-radius: 8px;
  font-family: 'Courier New', monospace;
  font-size: 0.9rem;
  color: #2c3e50;
}

.model-badge {
  background: linear-gradient(135deg, #6c5ce7 0%, #5f3dc4 100%);
  color: white;
  padding: 0.5rem 1rem;
  border-radius: 8px;
  font-size: 0.9rem;
  font-weight: 600;
  box-shadow: 0 3px 10px rgba(108, 92, 231, 0.3);
}

@media (max-width: 1200px) {
  .test-container {
    grid-template-columns: 1fr;
    max-width: 800px;
  }
  
  .transcribe-test {
    padding: 0.5rem;
  }
}

@media (max-width: 768px) {
  .transcribe-test {
    padding: 0.5rem;
  }
  
  .page-header h1 {
    font-size: 2rem;
  }
  
  .upload-section, .result-section, .api-info {
    padding: 1.5rem;
  }
  
  .upload-controls {
    flex-direction: column;
  }
  
  .result-actions {
    flex-direction: column;
  }
  
  .info-grid {
    grid-template-columns: 1fr;
  }
  
  .upload-area {
    padding: 2rem 1rem;
  }
  
  .file-input-label, .transcribe-btn {
    padding: 1rem 1.5rem;
  }
}

@media (max-width: 480px) {
  .upload-placeholder .upload-icon,
  .file-info .file-icon {
    font-size: 3rem;
  }
  
  .section-header h3 {
    font-size: 1.2rem;
  }
  
  .result-text {
    font-size: 1rem;
    padding: 1.5rem;
  }
}
</style> 