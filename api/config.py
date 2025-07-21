import os
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings
import logging

class Settings(BaseSettings):
    """应用配置管理器"""
    
    # API配置
    transcribe_url: str = Field(default="http://221.181.122.58:23006/v1/audio/transcriptions", env="TRANSCRIBE_URL")
    llm_url: str = Field(default="https://api.chatanywhere.tech/v1/chat/completions", env="LLM_URL")
    llm_api_key: str = Field(..., env="LLM_API_KEY")  # 必填
    tts_url: str = Field(default="http://221.181.122.58:23006/v1/audio/speech", env="TTS_URL")
    
    # 服务器配置
    host: str = Field(default="127.0.0.1", env="HOST")
    port: int = Field(default=8000, env="PORT")
    debug: bool = Field(default=False, env="DEBUG")
    
    # 音频处理配置 - 优化实时性
    max_segment_len: int = Field(default=25, env="MAX_SEGMENT_LEN")  # 减少最大分段长度
    min_segment_len: int = Field(default=4, env="MIN_SEGMENT_LEN")   # 减少最小分段长度
    audio_sample_rate: int = Field(default=16000, env="AUDIO_SAMPLE_RATE")
    audio_chunk_duration: float = Field(default=0.5, env="AUDIO_CHUNK_DURATION")  # 减少录音分片时间
    
    # VAD配置 - 新增
    vad_silence_threshold: int = Field(default=10, env="VAD_SILENCE_THRESHOLD")
    vad_silence_duration: int = Field(default=800, env="VAD_SILENCE_DURATION")  # 静音检测时长(ms)
    vad_min_speech_duration: int = Field(default=300, env="VAD_MIN_SPEECH_DURATION")  # 最小说话时长(ms)
    
    # 音频过滤配置 - 新增
    min_audio_size: int = Field(default=200, env="MIN_AUDIO_SIZE")  # 最小音频数据大小（降低以接受更小的音频片段）
    max_audio_buffer_size: int = Field(default=20, env="MAX_AUDIO_BUFFER_SIZE")  # 最大音频缓冲区大小
    
    # 超时配置 - 优化
    transcribe_timeout: float = Field(default=5.0, env="TRANSCRIBE_TIMEOUT")
    llm_timeout: float = Field(default=15.0, env="LLM_TIMEOUT")
    tts_timeout: float = Field(default=8.0, env="TTS_TIMEOUT")
    
    # 并发控制配置 - 新增
    max_concurrent_tts: int = Field(default=3, env="MAX_CONCURRENT_TTS")
    http_max_connections: int = Field(default=10, env="HTTP_MAX_CONNECTIONS")
    
    # WebSocket配置
    ws_max_size: int = Field(default=10*1024*1024, env="WS_MAX_SIZE")
    ws_timeout: int = Field(default=60, env="WS_TIMEOUT")
    
    # LLM优化配置 - 新增
    llm_max_tokens: int = Field(default=1000, env="LLM_MAX_TOKENS")  # 限制输出长度
    llm_temperature: float = Field(default=0.7, env="LLM_TEMPERATURE")
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # 忽略额外的字段

# 全局配置实例
settings = None

def get_settings() -> Settings:
    """获取配置实例（单例模式）"""
    global settings
    if settings is None:
        try:
            settings = Settings()
        except Exception as e:
            logging.error(f"Failed to load settings: {e}")
            logging.error("Please ensure you have created a .env file based on config.env.template")
            raise
    return settings

def get_llm_headers() -> dict:
    """获取LLM API headers"""
    config = get_settings()
    return {
        'Authorization': f'Bearer {config.llm_api_key}',
        'Content-Type': 'application/json'
    }
 