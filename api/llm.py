import httpx
import json
import logging
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Union
from .config import get_settings, get_llm_headers

# 配置日志
logger = logging.getLogger(__name__)

router = APIRouter()
config = get_settings()

class Message(BaseModel):
    """消息模型"""
    role: str = Field(..., description="角色: system, user, assistant")
    content: str = Field(..., description="消息内容")

class ChatRequest(BaseModel):
    """聊天请求模型"""
    model: str = Field(default="gpt-4o-ca", description="使用的模型")
    messages: List[Message] = Field(..., description="对话消息列表")
    temperature: Optional[float] = Field(default=0.7, description="温度参数")
    max_tokens: Optional[int] = Field(default=1000, description="最大tokens")
    stream: Optional[bool] = Field(default=False, description="是否流式输出")
    top_p: Optional[float] = Field(default=1.0, description="top_p参数")
    frequency_penalty: Optional[float] = Field(default=0.0, description="频率惩罚")
    presence_penalty: Optional[float] = Field(default=0.0, description="存在惩罚")

class ChatResponse(BaseModel):
    """聊天响应模型"""
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[Dict[str, Any]]
    usage: Optional[Dict[str, int]] = None

class CompletionRequest(BaseModel):
    """文本补全请求模型"""
    model: str = Field(default="gpt-4o-ca", description="使用的模型")
    prompt: str = Field(..., description="输入提示")
    max_tokens: Optional[int] = Field(default=1000, description="最大tokens")
    temperature: Optional[float] = Field(default=0.7, description="温度参数")
    top_p: Optional[float] = Field(default=1.0, description="top_p参数")
    stream: Optional[bool] = Field(default=False, description="是否流式输出")

async def llm_request_with_retry(
    payload: dict,
    max_retries: int = 3,
    stream: bool = False
) -> Union[dict, httpx.Response]:
    """带重试机制的LLM请求"""
    
    timeout = httpx.Timeout(config.ws_timeout)
    headers = get_llm_headers()
    
    for attempt in range(max_retries):
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                if stream:
                    # 流式请求
                    response = await client.post(
                        config.llm_url,
                        headers=headers,
                        json=payload,
                        timeout=None  # 流式请求不设置超时
                    )
                    response.raise_for_status()
                    return response
                else:
                    # 非流式请求
                    response = await client.post(
                        config.llm_url,
                        headers=headers,
                        json=payload,
                        timeout=60
                    )
                    response.raise_for_status()
                    return response.json()
                    
        except httpx.TimeoutException:
            logger.warning(f"LLM请求超时 (尝试 {attempt + 1}/{max_retries})")
            if attempt == max_retries - 1:
                raise HTTPException(status_code=408, detail="LLM请求超时")
        except httpx.HTTPStatusError as e:
            logger.warning(f"LLM HTTP错误 (尝试 {attempt + 1}/{max_retries}): {e}")
            if attempt == max_retries - 1:
                try:
                    error_detail = e.response.json()
                except:
                    error_detail = e.response.text
                raise HTTPException(
                    status_code=e.response.status_code,
                    detail=f"LLM服务错误: {error_detail}"
                )
        except Exception as e:
            logger.warning(f"LLM请求失败 (尝试 {attempt + 1}/{max_retries}): {e}")
            if attempt == max_retries - 1:
                raise HTTPException(status_code=500, detail=f"LLM服务异常: {str(e)}")
    
    raise HTTPException(status_code=500, detail="LLM服务达到最大重试次数")

def validate_messages(messages: List[Message]) -> None:
    """验证消息格式"""
    if not messages:
        raise HTTPException(status_code=400, detail="消息列表不能为空")
    
    valid_roles = {"system", "user", "assistant"}
    for i, message in enumerate(messages):
        if message.role not in valid_roles:
            raise HTTPException(
                status_code=400,
                detail=f"消息 {i} 的角色 '{message.role}' 无效"
            )
        
        if not message.content.strip():
            raise HTTPException(
                status_code=400,
                detail=f"消息 {i} 的内容不能为空"
            )

@router.post("/chat/completions")
async def chat_completions(request: ChatRequest):
    """
    聊天补全API
    
    Args:
        request: 聊天请求参数
        
    Returns:
        ChatResponse 或 StreamingResponse: 聊天响应
    """
    try:
        # 验证消息
        validate_messages(request.messages)
        
        logger.info(f"处理聊天请求: 模型={request.model}, 消息数={len(request.messages)}, 流式={request.stream}")
        
        # 构建请求payload
        payload = {
            "model": request.model,
            "messages": [msg.dict() for msg in request.messages],
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
            "stream": request.stream,
            "top_p": request.top_p,
            "frequency_penalty": request.frequency_penalty,
            "presence_penalty": request.presence_penalty
        }
        
        if request.stream:
            # 流式响应
            response = await llm_request_with_retry(payload, stream=True)
            
            async def generate_stream():
                try:
                    async for line in response.aiter_lines():
                        if line.strip():
                            yield f"{line}\n"
                except Exception as e:
                    logger.error(f"流式响应处理错误: {e}")
                    yield f"data: {json.dumps({'error': str(e)})}\n\n"
                finally:
                    yield "data: [DONE]\n\n"
            
            return StreamingResponse(
                generate_stream(),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive"
                }
            )
        else:
            # 非流式响应
            result = await llm_request_with_retry(payload, stream=False)
            logger.info("聊天请求处理完成")
            return result
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"聊天处理异常: {e}")
        raise HTTPException(status_code=500, detail=f"服务器内部错误: {str(e)}")

@router.post("/completions")
async def text_completions(request: CompletionRequest):
    """
    文本补全API
    
    Args:
        request: 补全请求参数
        
    Returns:
        响应或StreamingResponse: 补全响应
    """
    try:
        # 验证输入
        if not request.prompt.strip():
            raise HTTPException(status_code=400, detail="提示文本不能为空")
        
        logger.info(f"处理文本补全请求: 模型={request.model}, 提示长度={len(request.prompt)}")
        
        # 将文本补全转换为聊天格式
        messages = [{"role": "user", "content": request.prompt}]
        
        payload = {
            "model": request.model,
            "messages": messages,
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
            "stream": request.stream,
            "top_p": request.top_p
        }
        
        if request.stream:
            # 流式响应
            response = await llm_request_with_retry(payload, stream=True)
            
            async def generate_stream():
                try:
                    async for line in response.aiter_lines():
                        if line.strip():
                            yield f"{line}\n"
                except Exception as e:
                    logger.error(f"流式响应处理错误: {e}")
                    yield f"data: {json.dumps({'error': str(e)})}\n\n"
                finally:
                    yield "data: [DONE]\n\n"
            
            return StreamingResponse(
                generate_stream(),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive"
                }
            )
        else:
            # 非流式响应
            result = await llm_request_with_retry(payload, stream=False)
            logger.info("文本补全请求处理完成")
            return result
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"文本补全处理异常: {e}")
        raise HTTPException(status_code=500, detail=f"服务器内部错误: {str(e)}")

@router.get("/llm/models")
async def get_available_llm_models():
    """获取可用的模型列表"""
    try:
        return {
            "object": "list",
            "data": [
                {
                    "id": "gpt-4o-ca",
                    "object": "model",
                    "created": 1677610602,
                    "owned_by": "chatanywhere",
                    "root": "gpt-4o-ca",
                    "parent": None,
                    "permission": []
                },
                {
                    "id": "gpt-3.5-turbo",
                    "object": "model",
                    "created": 1677610602,
                    "owned_by": "openai",
                    "root": "gpt-3.5-turbo",
                    "parent": None,
                    "permission": []
                }
            ]
        }
    except Exception as e:
        logger.error(f"获取模型列表失败: {e}")
        raise HTTPException(status_code=500, detail="获取模型列表失败")

@router.get("/usage")
async def get_usage_stats():
    """获取使用统计 (占位符)"""
    try:
        return {
            "total_requests": 0,
            "total_tokens": 0,
            "status": "healthy"
        }
    except Exception as e:
        logger.error(f"获取使用统计失败: {e}")
        raise HTTPException(status_code=500, detail="获取使用统计失败") 