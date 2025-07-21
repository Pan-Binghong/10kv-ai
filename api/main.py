from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import logging
from .config import get_settings
from . import realtime, tts, transcription, llm, mock_llm

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 获取配置
config = get_settings()

app = FastAPI(
    title="10KV AI Real-time Voice Chat API",
    description="实时语音对话系统API",
    version="1.0.0",
    debug=config.debug
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生产环境中应该限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(realtime.router, prefix="/api/v1")
app.include_router(tts.router, prefix="/api/v1")
app.include_router(transcription.router, prefix="/api/v1")
app.include_router(llm.router, prefix="/api/v1")
app.include_router(mock_llm.router, prefix="/api/v1")

@app.get("/")
async def root():
    """健康检查端点"""
    return {
        "message": "10KV AI Real-time Voice Chat API is running",
        "version": "1.0.0",
        "status": "healthy"
    }

@app.get("/health")
async def health_check():
    """详细的健康检查"""
    return {
        "status": "healthy",
        "services": {
            "api": "running",
            "websocket": "available",
            "config": "loaded"
        }
    }

if __name__ == "__main__":
    logger.info(f"启动服务器 - Host: {config.host}, Port: {config.port}")
    uvicorn.run(
        "api.main:app",
        host=config.host,
        port=config.port,
        log_level="info" if not config.debug else "debug",
        reload=config.debug
    ) 