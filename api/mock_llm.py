import json
import asyncio
import random
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

class ChatMessage(BaseModel):
    role: str
    content: str

class MockChatRequest(BaseModel):
    model: str = "mock-gpt"
    messages: List[ChatMessage]
    stream: bool = False

# 预设的回复模板
MOCK_RESPONSES = [
    "好的，我理解您说的'{content}'。这是一个很有趣的话题！",
    "关于'{content}'，我觉得这确实值得深入思考。",
    "您提到的'{content}'让我想到了很多相关的内容。",
    "我明白您说的'{content}'，让我来回应一下这个问题。",
    "针对'{content}'这个话题，我有一些想法想和您分享。",
    "'{content}'确实是个不错的观点，我们可以进一步讨论。",
    "我听到您说了'{content}'，这确实很有意思。",
    "关于'{content}'，我想分享一些我的理解。",
]

def generate_mock_response(user_content: str) -> str:
    """生成模拟回复"""
    template = random.choice(MOCK_RESPONSES)
    response = template.format(content=user_content[:20] + "..." if len(user_content) > 20 else user_content)
    
    # 添加一些随机的扩展内容
    extensions = [
        "希望这个回答对您有帮助。",
        "如果您还有其他问题，请随时告诉我。",
        "我们可以继续深入探讨这个话题。",
        "感谢您与我分享这个想法。",
        "这确实是一个值得思考的问题。",
    ]
    
    if random.random() > 0.3:  # 70%的概率添加扩展
        response += " " + random.choice(extensions)
    
    return response

async def stream_mock_response(content: str):
    """流式返回模拟回复"""
    response_text = generate_mock_response(content)
    
    # 将回复分成小块进行流式传输
    words = response_text.split()
    
    for i, word in enumerate(words):
        chunk_data = {
            "id": f"mock-{random.randint(1000, 9999)}",
            "object": "chat.completion.chunk",
            "created": 1677652288,
            "model": "mock-gpt",
            "choices": [{
                "index": 0,
                "delta": {
                    "content": word + (" " if i < len(words) - 1 else "")
                },
                "finish_reason": None
            }]
        }
        
        yield f"data: {json.dumps(chunk_data, ensure_ascii=False)}\n\n"
        await asyncio.sleep(0.1)  # 模拟真实的流式延迟
    
    # 发送结束标记
    final_chunk = {
        "id": f"mock-{random.randint(1000, 9999)}",
        "object": "chat.completion.chunk",
        "created": 1677652288,
        "model": "mock-gpt",
        "choices": [{
            "index": 0,
            "delta": {},
            "finish_reason": "stop"
        }]
    }
    
    yield f"data: {json.dumps(final_chunk, ensure_ascii=False)}\n\n"
    yield "data: [DONE]\n\n"

@router.post("/mock/chat/completions")
async def mock_chat_completions(request: MockChatRequest):
    """模拟聊天API"""
    try:
        # 获取用户的最后一条消息
        user_message = ""
        for msg in reversed(request.messages):
            if msg.role == "user":
                user_message = msg.content
                break
        
        if not user_message:
            user_message = "默认消息"
        
        logger.info(f"Mock LLM 收到请求: {user_message}")
        
        if request.stream:
            # 流式响应
            return StreamingResponse(
                stream_mock_response(user_message),
                media_type="text/plain",
                headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
            )
        else:
            # 非流式响应
            response_text = generate_mock_response(user_message)
            return {
                "id": f"mock-{random.randint(1000, 9999)}",
                "object": "chat.completion",
                "created": 1677652288,
                "model": "mock-gpt",
                "choices": [{
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": response_text
                    },
                    "finish_reason": "stop"
                }],
                "usage": {
                    "prompt_tokens": len(user_message.split()),
                    "completion_tokens": len(response_text.split()),
                    "total_tokens": len(user_message.split()) + len(response_text.split())
                }
            }
            
    except Exception as e:
        logger.error(f"Mock LLM 处理异常: {e}")
        return {"error": {"message": f"Mock服务错误: {str(e)}", "type": "mock_error"}}

@router.get("/mock/models")
async def mock_models():
    """返回模拟的模型列表"""
    return {
        "object": "list",
        "data": [{
            "id": "mock-gpt",
            "object": "model",
            "created": 1677610602,
            "owned_by": "mock",
            "root": "mock-gpt",
            "parent": None,
            "permission": []
        }]
    } 