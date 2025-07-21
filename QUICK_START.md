# 🚀 10KV AI 实时语音对话系统 - 快速入门

## 📋 系统概述

优化后的10KV AI实时语音对话系统具备以下特性：

- ✅ **安全可靠**: 移除硬编码密钥，环境变量配置
- ✅ **性能优化**: 异步处理，自动重试机制
- ✅ **内存管理**: 自动资源清理，无内存泄漏
- ✅ **错误处理**: 完善的错误恢复和用户提示
- ✅ **易于部署**: 统一配置管理，健康检查

## 🛠️ 快速启动 (3分钟)

### 1️⃣ 环境准备

```bash
# 1. 克隆项目 (如果需要)
git clone <your-repo-url>
cd 10kv-ai

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置环境变量
cp config.env.template .env
```

### 2️⃣ 配置API密钥

编辑 `.env` 文件，填入你的API配置：

```bash
# 必填：LLM API密钥
LLM_API_KEY=your_openai_api_key_here

# 可选：其他配置项已有默认值
TRANSCRIBE_URL=http://221.181.122.58:23006/v1/audio/transcriptions
TTS_URL=http://221.181.122.58:23006/v1/audio/speech
```

### 3️⃣ 启动服务

```bash
# 方式1: 使用启动脚本 (推荐)
python start_server.py

# 方式2: 直接启动
python -m api.main

# 方式3: 开发模式
uvicorn api.main:app --host 127.0.0.1 --port 8000 --reload
```

### 4️⃣ 验证安装

```bash
# 运行系统测试
python test_system.py

# 检查服务状态
curl http://127.0.0.1:8000/health
```

## 🌐 访问地址

启动成功后，你可以访问：

- **API文档**: http://127.0.0.1:8000/docs
- **健康检查**: http://127.0.0.1:8000/health
- **WebSocket**: ws://127.0.0.1:8000/api/v1/ws/realtime
- **前端界面**: `web-ui/web-vue-demo/src/components/RealtimeVoiceChat.vue`

## 📱 前端使用

### Vue.js 组件

```vue
<template>
  <RealtimeVoiceChat />
</template>

<script>
import RealtimeVoiceChat from './components/RealtimeVoiceChat.vue'

export default {
  components: {
    RealtimeVoiceChat
  }
}
</script>
```

### 直接HTML使用

```html
<!DOCTYPE html>
<html>
<head>
    <title>语音对话测试</title>
</head>
<body>
    <div id="app">
        <!-- 复制 RealtimeVoiceChat.vue 的 template 内容 -->
    </div>
    <script src="path/to/vue.js"></script>
    <script>
        // 复制组件的JavaScript代码
    </script>
</body>
</html>
```

## 🔧 配置说明

### 环境变量列表

| 变量名 | 说明 | 默认值 | 必填 |
|--------|------|--------|------|
| `LLM_API_KEY` | LLM API密钥 | - | ✅ |
| `TRANSCRIBE_URL` | 转录服务地址 | 已提供 | ❌ |
| `LLM_URL` | LLM服务地址 | 已提供 | ❌ |
| `TTS_URL` | TTS服务地址 | 已提供 | ❌ |
| `HOST` | 服务器主机 | 127.0.0.1 | ❌ |
| `PORT` | 服务器端口 | 8000 | ❌ |
| `DEBUG` | 调试模式 | false | ❌ |

### 高级配置

```bash
# 性能配置
MAX_SEGMENT_LEN=30          # 最大分段长度
MIN_SEGMENT_LEN=5           # 最小分段长度
WS_TIMEOUT=60              # WebSocket超时时间
WS_MAX_SIZE=10485760       # WebSocket最大消息大小

# 音频配置
AUDIO_SAMPLE_RATE=16000    # 音频采样率
AUDIO_CHUNK_DURATION=1.5   # 音频分片时长
```

## 🐛 常见问题

### Q1: 启动时提示"缺少依赖包"

```bash
# 解决方案：安装所有依赖
pip install -r requirements.txt

# 如果还有问题，尝试升级pip
pip install --upgrade pip
pip install -r requirements.txt
```

### Q2: 配置加载失败

```bash
# 检查.env文件是否存在
ls -la .env

# 检查API密钥是否正确配置
cat .env | grep LLM_API_KEY
```

### Q3: WebSocket连接失败

```bash
# 检查服务器是否启动
curl http://127.0.0.1:8000/health

# 检查端口是否被占用
netstat -an | grep 8000
```

### Q4: 前端无法连接

```javascript
// 检查前端WebSocket地址是否正确
const ws = new WebSocket('ws://127.0.0.1:8000/api/v1/ws/realtime')
```

## 📊 系统监控

### 健康检查

```bash
# 简单检查
curl http://127.0.0.1:8000/health

# 详细检查
curl http://127.0.0.1:8000/health | jq
```

### 日志查看

服务器会输出详细的运行日志，包括：

- 🔍 请求处理状态
- ⚠️ 错误和警告信息
- 📈 性能统计数据
- 🔄 重试和恢复过程

## 🚀 生产部署建议

### 1. 安全配置

```bash
# 生产环境配置
DEBUG=false
HOST=0.0.0.0  # 仅在安全的内网环境中使用

# 使用HTTPS
# 配置反向代理 (Nginx/Apache)
```

### 2. 性能优化

```bash
# 使用Gunicorn部署
pip install gunicorn
gunicorn api.main:app -w 4 -k uvicorn.workers.UvicornWorker
```

### 3. 监控和日志

```bash
# 集成专业日志系统
# 添加性能监控
# 设置告警机制
```

## 📞 技术支持

如果遇到问题：

1. 📖 查看 `OPTIMIZATION_SUMMARY.md` 了解详细优化内容
2. 🔧 运行 `test_system.py` 检查系统状态  
3. 📋 查看服务器日志获取错误信息
4. 🛠️ 检查配置文件和环境变量

---

🎉 **恭喜！你的10KV AI实时语音对话系统已经准备就绪！** 