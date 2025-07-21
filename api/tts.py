import httpx
import io
import logging
from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
from .config import get_settings

# 配置日志
logger = logging.getLogger(__name__)

router = APIRouter()
config = get_settings()

class TTSRequest(BaseModel):
    """TTS请求模型"""
    model: str = "ChatTTS"
    input: str
    voice: Optional[str] = None
    speed: Optional[float] = 1.0
    format: Optional[str] = "wav"

class TTSResponse(BaseModel):
    """TTS响应模型"""
    success: bool
    message: str
    audio_length: Optional[int] = None

async def tts_with_retry(request: TTSRequest, max_retries: int = 3):
    """带重试机制的TTS请求"""
    payload = {
        "model": request.model,
        "input": request.input,
        "voice": request.voice or "AAAAANGeZ1UCAAAAAgAAAA8AAAAAAAAAAAAAAAAA0A0AAGFyY2hpdmUvdmVyc2lvblBLAQIAAAAACAgAAAAAAABOREdMKAAAACgAAAAeAAAAAAAAAAAAAAAAAFIOAABhcmNoaXZlLy5kYXRhL3NlcmlhbGl6YXRpb25faWRQSwYGLAAAAAAAAAAeAy0AAAAAAAAAAAAFAAAAAAAAAAUAAAAAAAAAQgEAAAAAAAD4DgAAAAAAAFBLBgcAAAAAOhAAAAAAAAABAAAAUEsFBgAAAAAFAAUAQgEAAPgOAAAAAA==",
        "speed": request.speed
    }
    
    timeout = httpx.Timeout(config.ws_timeout)
    
    for attempt in range(max_retries):
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(config.tts_url, json=payload, timeout=30)
                response.raise_for_status()
                
                if response.status_code == 200:
                    content = response.content
                    if len(content) == 0:
                        raise ValueError("TTS服务返回空音频")
                    return content
                else:
                    raise HTTPException(
                        status_code=response.status_code,
                        detail=f"TTS服务错误: {response.text}"
                    )
                    
        except httpx.TimeoutException:
            logger.warning(f"TTS请求超时 (尝试 {attempt + 1}/{max_retries})")
            if attempt == max_retries - 1:
                raise HTTPException(status_code=408, detail="TTS请求超时")
        except httpx.HTTPStatusError as e:
            logger.warning(f"TTS HTTP错误 (尝试 {attempt + 1}/{max_retries}): {e}")
            if attempt == max_retries - 1:
                raise HTTPException(
                    status_code=e.response.status_code,
                    detail=f"TTS服务错误: {e.response.text}"
                )
        except Exception as e:
            logger.warning(f"TTS请求失败 (尝试 {attempt + 1}/{max_retries}): {e}")
            if attempt == max_retries - 1:
                raise HTTPException(status_code=500, detail=f"TTS服务异常: {str(e)}")
    
    raise HTTPException(status_code=500, detail="TTS服务达到最大重试次数")

@router.post("/speech", response_class=StreamingResponse)
async def tts_speech(request: TTSRequest):
    """
    文本转语音 API
    
    Args:
        request: TTS请求参数
        
    Returns:
        StreamingResponse: 音频流
    """
    try:
        # 输入验证
        if not request.input or not request.input.strip():
            raise HTTPException(status_code=400, detail="输入文本不能为空")
        
        if len(request.input) > 1000:  # 限制文本长度
            raise HTTPException(status_code=400, detail="文本长度不能超过1000字符")
        
        logger.info(f"处理TTS请求: 模型={request.model}, 文本长度={len(request.input)}")
        
        # 调用TTS服务
        audio_content = await tts_with_retry(request)
        
        logger.info(f"TTS处理完成，音频大小: {len(audio_content)} bytes")
        
        # 创建流式响应
        def generate():
            yield audio_content
        
        # 根据格式设置媒体类型
        media_type = "audio/wav" if request.format == "wav" else "application/octet-stream"
        
        return StreamingResponse(
            generate(),
            media_type=media_type,
            headers={
                "Content-Length": str(len(audio_content)),
                "Content-Disposition": f"attachment; filename=speech.{request.format}",
                "Cache-Control": "no-cache"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"TTS处理异常: {e}")
        raise HTTPException(status_code=500, detail=f"服务器内部错误: {str(e)}")

@router.post("/speech/stream")
async def tts_speech_stream(request: TTSRequest):
    """
    流式文本转语音 API
    
    Args:
        request: TTS请求参数
        
    Returns:
        StreamingResponse: 流式音频响应
    """
    try:
        # 输入验证
        if not request.input or not request.input.strip():
            raise HTTPException(status_code=400, detail="输入文本不能为空")
        
        logger.info(f"处理流式TTS请求: {request.input[:50]}...")
        
        payload = {
            "model": request.model,
            "input": request.input,
            "voice": request.voice,
            "speed": request.speed,
            "stream": True  # 启用流式响应
        }
        
        timeout = httpx.Timeout(config.ws_timeout)
        
        async def generate_audio_stream():
            try:
                async with httpx.AsyncClient(timeout=timeout) as client:
                    async with client.stream("POST", config.tts_url, json=payload) as response:
                        response.raise_for_status()
                        
                        async for chunk in response.aiter_bytes():
                            if chunk:
                                yield chunk
                                
            except Exception as e:
                logger.error(f"流式TTS错误: {e}")
                raise HTTPException(status_code=500, detail=f"流式TTS失败: {str(e)}")
        
        return StreamingResponse(
            generate_audio_stream(),
            media_type="audio/wav",
            headers={"Cache-Control": "no-cache"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"流式TTS处理异常: {e}")
        raise HTTPException(status_code=500, detail=f"服务器内部错误: {str(e)}")

@router.get("/voices")
async def get_available_voices():
    """获取可用的语音列表"""
    try:
        # 这里可以调用TTS服务的语音列表API
        # 暂时返回默认配置
        return {
            "voices": [
                {
                    "id": "default",
                    "name": "默认语音",
                    "language": "zh-CN",
                    "gender": "female"
                }
            ]
        }
    except Exception as e:
        logger.error(f"获取语音列表失败: {e}")
        raise HTTPException(status_code=500, detail="获取语音列表失败") 