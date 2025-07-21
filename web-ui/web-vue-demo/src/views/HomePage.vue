<template>
  <div class="home-page">
    <div class="header">
      <h1>🎤 10KV-AI 语音交互平台</h1>
      <p>选择下方功能进行测试</p>
    </div>
    
    <div class="nav-grid">
      <router-link to="/transcribe" class="nav-card transcribe">
        <div class="icon">📝</div>
        <h3>语音转录测试</h3>
        <p>上传音频文件，测试语音转文字功能</p>
        <div class="features">
          <span class="feature">• WAV格式支持</span>
          <span class="feature">• 16kHz采样率</span>
          <span class="feature">• 中文识别</span>
        </div>
      </router-link>
      
      <router-link to="/llm" class="nav-card llm">
        <div class="icon">🧠</div>
        <h3>LLM对话测试</h3>
        <p>测试大语言模型对话功能</p>
        <div class="features">
          <span class="feature">• GPT-4模型</span>
          <span class="feature">• 流式响应</span>
          <span class="feature">• 中文对话</span>
        </div>
      </router-link>
      
      <router-link to="/tts" class="nav-card tts">
        <div class="icon">🎵</div>
        <h3>语音合成测试</h3>
        <p>输入文字，生成语音音频</p>
        <div class="features">
          <span class="feature">• CosyVoice2引擎</span>
          <span class="feature">• 多语言支持</span>
          <span class="feature">• 自然语调</span>
          <span class="feature">• WAV输出</span>
        </div>
      </router-link>
      
      <router-link to="/realtime" class="nav-card realtime">
        <div class="icon">🚀</div>
        <h3>实时语音对话</h3>
        <p>完整的实时语音交互体验</p>
        <div class="features">
          <span class="feature">• 实时VAD检测</span>
          <span class="feature">• 流式处理</span>
          <span class="feature">• 完整对话链路</span>
        </div>
      </router-link>
    </div>
    
    <div class="footer">
      <p>💡 建议在安静环境下使用，确保麦克风权限已开启</p>
    </div>
  </div>
</template>

<script setup>
// 不需要额外的逻辑，纯展示组件
</script>

<style scoped>
.home-page {
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem;
  font-family: 'Segoe UI', 'PingFang SC', 'Microsoft YaHei', Arial, sans-serif;
}

.header {
  text-align: center;
  margin-bottom: 3rem;
}

.header h1 {
  color: #2c3e50;
  margin-bottom: 0.5rem;
  font-size: 2.5rem;
}

.header p {
  color: #7f8c8d;
  font-size: 1.1rem;
}

.nav-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 2rem;
  margin-bottom: 3rem;
}

.nav-card {
  background: white;
  border-radius: 16px;
  padding: 2rem;
  text-decoration: none;
  color: inherit;
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.08);
  transition: all 0.3s ease;
  border: 2px solid transparent;
  position: relative;
  overflow: hidden;
}

.nav-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 4px;
  transition: all 0.3s ease;
}

.nav-card.transcribe::before {
  background: linear-gradient(90deg, #74b9ff, #0984e3);
}

.nav-card.llm::before {
  background: linear-gradient(90deg, #fd79a8, #e84393);
}

.nav-card.tts::before {
  background: linear-gradient(90deg, #fdcb6e, #e17055);
}

.nav-card.realtime::before {
  background: linear-gradient(90deg, #55a3ff, #1e3799);
}

.nav-card:hover {
  transform: translateY(-8px);
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.15);
}

.nav-card:hover::before {
  height: 8px;
}

.icon {
  font-size: 3rem;
  margin-bottom: 1rem;
  text-align: center;
}

.nav-card h3 {
  margin: 0 0 1rem 0;
  color: #2c3e50;
  font-size: 1.3rem;
  text-align: center;
}

.nav-card p {
  color: #7f8c8d;
  margin-bottom: 1.5rem;
  text-align: center;
  line-height: 1.5;
}

.features {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.feature {
  color: #95a5a6;
  font-size: 0.9rem;
  padding-left: 0.5rem;
}

.footer {
  text-align: center;
  color: #95a5a6;
  font-style: italic;
}

@media (max-width: 768px) {
  .nav-grid {
    grid-template-columns: 1fr;
    gap: 1.5rem;
  }
  
  .nav-card {
    padding: 1.5rem;
  }
  
  .header h1 {
    font-size: 2rem;
  }
}</style> 