# 🎤 10KV AI 实时语音对话系统

一个基于FastAPI和WebSocket的实时AI语音对话系统，支持语音转文字、AI对话和文字转语音功能。

## ✨ 主要功能

- 🎙️ **实时语音识别**：将语音实时转换为文字
- 🤖 **AI智能对话**：集成大语言模型进行智能对话
- 🔊 **文字转语音**：将AI回复转换为自然语音
- 🌐 **WebSocket实时通信**：低延迟的实时交互体验
- 🎨 **Vue.js前端界面**：现代化的用户交互界面
- 🔒 **安全配置管理**：环境变量管理API密钥
- 📊 **健康检查和监控**：完善的系统状态监控

## 🏗️ 技术栈

### 后端
- **FastAPI** - 现代Python Web框架
- **WebSocket** - 实时双向通信
- **uvicorn** - ASGI服务器
- **pydantic** - 数据验证
- **structlog** - 结构化日志

### 前端
- **Vue.js 3** - 响应式前端框架
- **Vite** - 构建工具
- **recorder-core** - 音频录制
- **Vue Router** - 路由管理

### AI服务
- **OpenAI API** - 大语言模型
- **自定义语音识别服务** - 语音转文字
- **自定义TTS服务** - 文字转语音

## 🚀 快速开始

### 1. 环境要求

- Python 3.11+
- Node.js 16+（用于前端开发）

### 2. 安装依赖

```bash
# 克隆项目
git clone <your-repo-url>
cd 10kv-ai

# 安装Python依赖
pip install -r requirements.txt

# 或使用uv（推荐）
uv sync
```

### 3. 配置环境变量

```bash
# 复制配置模板
cp config.env.template .env

# 编辑.env文件，添加你的API密钥
# LLM_API_KEY=your_openai_api_key_here
```

### 4. 启动服务

```bash
# 使用启动脚本
python start_server.py

# 或直接启动
python -m api.main

# 开发模式
uvicorn api.main:app --host 127.0.0.1 --port 8000 --reload
```

### 5. 前端开发（可选）

```bash
cd web-ui/web-vue-demo

# 安装前端依赖
npm install

# 启动开发服务器
npm run dev
```

## 📋 API文档

启动服务后，访问以下地址：

- **API文档**: http://127.0.0.1:8000/docs
- **健康检查**: http://127.0.0.1:8000/health
- **WebSocket端点**: ws://127.0.0.1:8000/api/v1/ws/realtime

## 🔧 配置说明

### 环境变量

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

## 📁 项目结构

```
10kv-ai/
├── api/                    # 后端API模块
│   ├── config.py          # 配置管理
│   ├── main.py            # FastAPI应用入口
│   ├── realtime.py        # WebSocket实时通信
│   ├── transcription.py   # 语音转文字
│   ├── llm.py             # 大语言模型接口
│   └── tts.py             # 文字转语音
├── web-ui/                 # 前端界面
│   └── web-vue-demo/      # Vue.js项目
├── script/                 # 工具脚本
├── tests/                  # 测试文件
├── requirements.txt        # Python依赖
├── pyproject.toml         # 项目配置
├── start_server.py        # 启动脚本
└── test_system.py         # 系统测试
```

## 🧪 测试

```bash
# 运行系统测试
python test_system.py

# 运行单元测试
pytest tests/
```

## 🔍 故障排除

### 常见问题

1. **启动时提示缺少依赖包**
   ```bash
   pip install -r requirements.txt
   ```

2. **API密钥配置错误**
   - 检查`.env`文件是否存在
   - 确认`LLM_API_KEY`已正确设置

3. **WebSocket连接失败**
   - 确认服务器已启动：`curl http://127.0.0.1:8000/health`
   - 检查端口是否被占用

4. **前端无法连接**
   - 检查WebSocket地址是否正确
   - 确认CORS设置允许前端域名

### 日志查看

服务器会输出详细的运行日志，包括：
- 🔍 请求处理状态
- ⚠️ 错误和警告信息
- 📈 性能统计数据
- 🔄 重试和恢复过程

## 🚀 生产部署

### 使用Gunicorn部署

```bash
pip install gunicorn
gunicorn api.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### 使用Docker部署

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["python", "start_server.py"]
```

## 📄 许可证

本项目采用 MIT 许可证。

## 🤝 贡献

欢迎提交Issue和Pull Request！

## 📞 技术支持

如果遇到问题，请：

1. 查看 [QUICK_START.md](QUICK_START.md) 快速开始指南
2. 查看 [OPTIMIZATION_SUMMARY.md](OPTIMIZATION_SUMMARY.md) 了解优化详情
3. 运行 `python test_system.py` 检查系统状态
4. 提交Issue描述问题详情

---

## 🌟 特性展示

- ⚡ **低延迟**：WebSocket实现毫秒级响应
- 🔧 **易扩展**：模块化设计，易于添加新功能
- 🛡️ **安全可靠**：完善的错误处理和重试机制
- 📱 **跨平台**：支持Windows、macOS、Linux
- 🎨 **用户友好**：直观的Web界面和API文档

**立即开始您的AI语音对话之旅！** 🎉
