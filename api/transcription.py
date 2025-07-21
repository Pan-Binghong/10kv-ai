import httpx
import io
import logging
from fastapi import APIRouter, File, UploadFile, HTTPException, Form
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional
from .config import get_settings

# 配置日志
logger = logging.getLogger(__name__)

router = APIRouter()
config = get_settings()

class TranscriptionResponse(BaseModel):
    """转录响应模型"""
    text: str
    language: Optional[str] = None
    confidence: Optional[float] = None
    duration: Optional[float] = None

class TranscriptionRequest(BaseModel):
    """转录请求模型"""
    model: str = "SenseVoiceSmall"
    language: Optional[str] = None
    prompt: Optional[str] = None
    response_format: str = "json"
    temperature: float = 0.0

async def transcribe_with_retry(
    file_content: bytes,
    filename: str,
    content_type: str,
    model: str = "SenseVoiceSmall",
    max_retries: int = 3
) -> dict:
    """带重试机制的音频转录"""
    
    timeout = httpx.Timeout(config.ws_timeout)
    
    for attempt in range(max_retries):
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                files = {
                    'file': (filename, io.BytesIO(file_content), content_type)
                }
                data = {
                    'model': model
                }
                
                response = await client.post(
                    config.transcribe_url,
                    files=files,
                    data=data,
                    timeout=30
                )
                response.raise_for_status()
                
                result = response.json()
                
                # 验证响应格式
                if not isinstance(result, dict):
                    raise ValueError("转录服务返回格式错误")
                
                # 确保有text字段
                if "text" not in result:
                    result["text"] = ""
                
                return result
                
        except httpx.TimeoutException:
            logger.warning(f"转录请求超时 (尝试 {attempt + 1}/{max_retries})")
            if attempt == max_retries - 1:
                raise HTTPException(status_code=408, detail="转录请求超时")
        except httpx.HTTPStatusError as e:
            logger.warning(f"转录HTTP错误 (尝试 {attempt + 1}/{max_retries}): {e}")
            if attempt == max_retries - 1:
                raise HTTPException(
                    status_code=e.response.status_code,
                    detail=f"转录服务错误: {e.response.text}"
                )
        except Exception as e:
            logger.warning(f"转录请求失败 (尝试 {attempt + 1}/{max_retries}): {e}")
            if attempt == max_retries - 1:
                raise HTTPException(status_code=500, detail=f"转录服务异常: {str(e)}")
    
    raise HTTPException(status_code=500, detail="转录服务达到最大重试次数")

def validate_audio_file(file: UploadFile) -> None:
    """验证音频文件"""
    
    # 检查文件大小 (限制为50MB)
    max_size = 50 * 1024 * 1024  # 50MB
    if file.size and file.size > max_size:
        raise HTTPException(
            status_code=413,
            detail=f"文件大小不能超过{max_size // (1024*1024)}MB"
        )
    
    # 检查文件类型
    allowed_types = {
        'audio/wav', 'audio/mp3', 'audio/mpeg', 'audio/m4a',
        'audio/ogg', 'audio/flac', 'video/mp4', 'video/mpeg',
        'video/webm'
    }
    
    if file.content_type and file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件类型: {file.content_type}"
        )
    
    # 检查文件扩展名
    if file.filename:
        allowed_extensions = {'.wav', '.mp3', '.m4a', '.ogg', '.flac', '.mp4', '.webm'}
        file_ext = '.' + file.filename.split('.')[-1].lower()
        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"不支持的文件扩展名: {file_ext}"
            )

@router.post("/audio/transcriptions", response_model=TranscriptionResponse)
async def transcribe_audio(
    file: UploadFile = File(..., description="音频文件"),
    model: str = Form(default="SenseVoiceSmall", description="转录模型"),
    language: Optional[str] = Form(default=None, description="音频语言"),
    prompt: Optional[str] = Form(default=None, description="转录提示"),
    response_format: str = Form(default="json", description="响应格式"),
    temperature: float = Form(default=0.0, description="温度参数")
):
    """
    音频转录API
    
    Args:
        file: 音频文件
        model: 转录模型
        language: 音频语言
        prompt: 转录提示
        response_format: 响应格式
        temperature: 温度参数
        
    Returns:
        TranscriptionResponse: 转录结果
    """
    try:
        # 验证文件
        validate_audio_file(file)
        
        logger.info(f"处理转录请求: 文件={file.filename}, 模型={model}")
        
        # 读取文件内容
        file_content = await file.read()
        
        if len(file_content) == 0:
            raise HTTPException(status_code=400, detail="文件内容为空")
        
        # 调用转录服务
        result = await transcribe_with_retry(
            file_content,
            file.filename or "audio.wav",
            file.content_type or "audio/wav",
            model
        )
        
        logger.info(f"转录完成: 文本长度={len(result.get('text', ''))}")
        
        # 构建响应
        response = TranscriptionResponse(
            text=result.get("text", ""),
            language=result.get("language"),
            confidence=result.get("confidence"),
            duration=result.get("duration")
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"转录处理异常: {e}")
        raise HTTPException(status_code=500, detail=f"服务器内部错误: {str(e)}")

@router.post("/audio/transcriptions/batch")
async def transcribe_audio_batch(
    files: list[UploadFile] = File(..., description="音频文件列表"),
    model: str = Form(default="SenseVoiceSmall", description="转录模型")
):
    """
    批量音频转录API
    
    Args:
        files: 音频文件列表
        model: 转录模型
        
    Returns:
        dict: 批量转录结果
    """
    try:
        if len(files) > 10:  # 限制批量文件数量
            raise HTTPException(status_code=400, detail="批量文件数量不能超过10个")
        
        logger.info(f"处理批量转录请求: {len(files)}个文件")
        
        results = []
        
        for i, file in enumerate(files):
            try:
                # 验证文件
                validate_audio_file(file)
                
                # 读取文件内容
                file_content = await file.read()
                
                # 调用转录服务
                result = await transcribe_with_retry(
                    file_content,
                    file.filename or f"audio_{i}.wav",
                    file.content_type or "audio/wav",
                    model
                )
                
                results.append({
                    "filename": file.filename,
                    "success": True,
                    "text": result.get("text", ""),
                    "language": result.get("language"),
                    "confidence": result.get("confidence"),
                    "duration": result.get("duration")
                })
                
            except Exception as e:
                logger.error(f"文件 {file.filename} 转录失败: {e}")
                results.append({
                    "filename": file.filename,
                    "success": False,
                    "error": str(e)
                })
        
        success_count = sum(1 for r in results if r.get("success", False))
        
        return {
            "total": len(files),
            "success": success_count,
            "failed": len(files) - success_count,
            "results": results
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"批量转录处理异常: {e}")
        raise HTTPException(status_code=500, detail=f"服务器内部错误: {str(e)}")

@router.get("/transcription/models")
async def get_available_transcription_models():
    """获取可用的转录模型列表"""
    try:
        return {
            "models": [
                {
                    "id": "SenseVoiceSmall",
                    "name": "SenseVoice Small",
                    "description": "轻量级语音识别模型",
                    "languages": ["zh", "en", "ja", "ko"]
                }
            ]
        }
    except Exception as e:
        logger.error(f"获取模型列表失败: {e}")
        raise HTTPException(status_code=500, detail="获取模型列表失败") 