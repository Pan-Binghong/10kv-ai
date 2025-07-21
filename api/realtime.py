import httpx
import asyncio
import io
import json
import time
import re
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from starlette.websockets import WebSocketState
from .config import get_settings, get_llm_headers

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

# 从配置获取设置
config = get_settings()

# 优化的分段策略：更简单，更快速
SPLIT_PATTERN = re.compile(r'[。！？.!?]')  # 简化标点符号匹配
QUICK_SPLIT_PATTERN = re.compile(r'[，、；;：:，]')  # 快速分段的辅助符号

# VAD改进：使用配置参数
SILENCE_THRESHOLD = config.vad_silence_threshold
SILENCE_DURATION = config.vad_silence_duration
MIN_SPEECH_DURATION = config.vad_min_speech_duration

def optimized_segment(text, last_idx=0, force_quick=False):
    """优化的分段：优先实时性，简化逻辑"""
    segments = []
    current_start = last_idx
    text_len = len(text)
    
    # 如果强制快速分段或文本较短，使用更激进的分段策略
    if force_quick or text_len - last_idx < config.max_segment_len * 2:
        # 查找主要标点符号
        main_punctuation = list(SPLIT_PATTERN.finditer(text[last_idx:]))
        
        for match in main_punctuation:
            end_pos = last_idx + match.end()
            segment = text[current_start:end_pos].strip()
            
            # 如果分段长度合适，直接添加
            if len(segment) >= config.min_segment_len:
                segments.append(segment)
                current_start = end_pos
                break  # 只取第一个合适的分段，提高速度
    
    # 如果没有找到合适的分段，检查辅助标点符号
    if not segments and text_len - current_start >= config.min_segment_len:
        aux_punctuation = list(QUICK_SPLIT_PATTERN.finditer(text[current_start:]))
        for match in aux_punctuation:
            end_pos = current_start + match.end()
            segment = text[current_start:end_pos].strip()
            if len(segment) >= config.min_segment_len:
                segments.append(segment)
                current_start = end_pos
                break
    
    # 如果仍然没有分段，且文本足够长，强制分段
    if not segments and text_len - current_start >= config.max_segment_len:
        segment = text[current_start:current_start + config.max_segment_len]
        segments.append(segment)
        current_start += config.max_segment_len
    
    return segments, current_start

async def safe_send_text(websocket: WebSocket, message: str):
    """安全发送文本消息"""
    if websocket.client_state == WebSocketState.CONNECTED:
        try:
            await websocket.send_text(message)
            return True
        except Exception as e:
            logger.error(f"发送文本消息失败: {e}")
            return False
    return False

async def safe_send_bytes(websocket: WebSocket, data: bytes):
    """安全发送字节数据"""
    if websocket.client_state == WebSocketState.CONNECTED:
        try:
            await websocket.send_bytes(data)
            return True
        except Exception as e:
            logger.error(f"发送字节数据失败: {e}")
            return False
    return False

async def transcribe_audio_with_retry(client: httpx.AsyncClient, audio_bytes: bytes, max_retries: int = 2):
    """优化的音频转录：减少重试次数"""
    for attempt in range(max_retries):
        try:
            files = {'file': ('audio.wav', io.BytesIO(audio_bytes), 'audio/wav')}
            data = {'model': 'SenseVoiceSmall'}
            
            response = await client.post(config.transcribe_url, files=files, data=data, timeout=config.transcribe_timeout)
            response.raise_for_status()
            
            result = response.json()
            text = result.get("text", "").strip()
            return text, None
            
        except Exception as e:
            logger.warning(f"转录失败 (尝试 {attempt + 1}/{max_retries}): {e}")
            if attempt == max_retries - 1:
                return None, f"转录失败: {e}"
            await asyncio.sleep(0.2 * (attempt + 1))  # 减少等待时间
    
    return None, "转录失败: 达到最大重试次数"

async def generate_tts_stream(client: httpx.AsyncClient, text: str, websocket: WebSocket):
    """优化的TTS生成：减少重试，快速失败"""
    tts_payload = {
        "model": "CosyVoice2-0.5B",
        "input": text,
        "voice": "中文女声"
    }
    
    try:
        # 使用配置的超时时间
        async with client.stream("POST", config.tts_url, json=tts_payload, timeout=config.tts_timeout) as tts_resp:
            if tts_resp.status_code == 200:
                logger.debug(f"TTS流式合成中: {text[:20]}...")
                chunk_count = 0
                async for chunk in tts_resp.aiter_bytes():
                    if websocket.client_state != WebSocketState.CONNECTED:
                        logger.info("WebSocket已断开，停止TTS流")
                        return False
                    if chunk:
                        chunk_count += 1
                        if not await safe_send_bytes(websocket, chunk):
                            return False
                        # 每发送几个chunk就让出控制权，避免阻塞
                        if chunk_count % 5 == 0:
                            await asyncio.sleep(0.001)
                return True
            else:
                error_text = await tts_resp.aread()
                logger.error(f"TTS失败 (状态码: {tts_resp.status_code}): {error_text}")
                return False
                
    except asyncio.TimeoutError:
        logger.warning(f"TTS请求超时: {text[:20]}...")
        await safe_send_text(websocket, json.dumps({"error": "TTS生成超时"}))
        return False
    except Exception as e:
        logger.error(f"TTS请求失败: {e}")
        await safe_send_text(websocket, json.dumps({"error": f"TTS生成失败: {e}"}))
        return False

async def process_llm_stream_optimized(client: httpx.AsyncClient, text: str, websocket: WebSocket):
    """优化的LLM流式处理"""
    llm_payload = {
        "model": "gpt-4o-ca",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant. Respond naturally and conversationally."},
            {"role": "user", "content": text}
        ],
        "stream": True,
        "max_tokens": config.llm_max_tokens,  # 使用配置参数
        "temperature": config.llm_temperature  # 使用配置参数
    }
    
    try:
        async with client.stream("POST", config.llm_url, headers=get_llm_headers(), json=llm_payload, timeout=config.llm_timeout) as llm_resp:
            if llm_resp.status_code != 200:
                error_text = await llm_resp.aread()
                error_msg = f"LLM API错误 (状态码: {llm_resp.status_code}): {error_text}"
                logger.error(error_msg)
                await safe_send_text(websocket, json.dumps({"error": error_msg}))
                return False
            
            llm_accum = ""
            last_idx = 0
            logger.debug("LLM流式输出中...")
            
            # 用于控制TTS任务
            tts_tasks = []
            segment_count = 0
            
            async for line in llm_resp.aiter_lines():
                if websocket.client_state != WebSocketState.CONNECTED:
                    logger.info("WebSocket已断开，终止LLM流式处理")
                    break
                    
                if not line.strip():
                    continue
                if line.startswith("data:"):
                    data = line[5:].strip()
                    if data == "[DONE]":
                        break
                    try:
                        obj = json.loads(data)
                        choices = obj.get("choices", [])
                        if not choices or "delta" not in choices[0]:
                            continue
                        delta = choices[0]["delta"].get("content", "")
                        if delta:
                            llm_accum += delta
                            # 使用优化的分段策略
                            force_quick = segment_count > 0  # 第一段之后使用快速分段
                            segs, new_last_idx = optimized_segment(llm_accum, last_idx, force_quick)
                            last_idx = new_last_idx
                            
                            for seg in segs:
                                if websocket.client_state != WebSocketState.CONNECTED:
                                    break
                                if seg.strip():  # 确保不发送空段
                                    logger.debug(f"LLM分段 #{segment_count}: {seg}")
                                    segment_count += 1
                                    
                                    # 发送LLM文本
                                    if not await safe_send_text(websocket, json.dumps({"type": "llm", "text": seg})):
                                        break
                                    
                                    # 并发处理TTS，不等待完成
                                    tts_task = asyncio.create_task(generate_tts_stream(client, seg, websocket))
                                    tts_tasks.append(tts_task)
                                    
                                    # 使用配置的并发限制
                                    if len(tts_tasks) > config.max_concurrent_tts:
                                        # 等待最早的任务完成
                                        await tts_tasks.pop(0)
                                    
                    except json.JSONDecodeError as e:
                        logger.warning(f"解析LLM流式数据出错: {e}")
                        continue
                    except Exception as e:
                        logger.error(f"处理LLM流式数据出错: {e}")
                        continue
            
            # 处理最后一段未分割的内容
            if last_idx < len(llm_accum) and websocket.client_state == WebSocketState.CONNECTED:
                seg = llm_accum[last_idx:].strip()
                if seg:
                    logger.debug(f"LLM尾段: {seg}")
                    if await safe_send_text(websocket, json.dumps({"type": "llm", "text": seg})):
                        tts_task = asyncio.create_task(generate_tts_stream(client, seg, websocket))
                        tts_tasks.append(tts_task)
            
            # 等待所有TTS任务完成（设置超时）
            if tts_tasks:
                try:
                    await asyncio.wait_for(asyncio.gather(*tts_tasks, return_exceptions=True), timeout=10.0)
                except asyncio.TimeoutError:
                    logger.warning("部分TTS任务超时")
            
            return True
            
    except asyncio.TimeoutError:
        logger.error("LLM请求超时")
        await safe_send_text(websocket, json.dumps({"error": "LLM处理超时"}))
        return False
    except Exception as e:
        logger.error(f"LLM流式处理失败: {e}")
        await safe_send_text(websocket, json.dumps({"error": f"LLM处理失败: {e}"}))
        return False

@router.websocket("/ws/realtime")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    logger.info("WebSocket 连接已建立")
    
    # 使用配置的超时和连接参数
    timeout = httpx.Timeout(connect=5.0, read=30.0, write=10.0, pool=5.0)
    limits = httpx.Limits(max_connections=config.http_max_connections)
    async with httpx.AsyncClient(timeout=timeout, limits=limits) as client:
        try:
            while True:
                logger.debug("等待接收消息...")
                try:
                    # 尝试接收文本消息（可能是ping）
                    message = await websocket.receive_text()
                    # 处理ping消息
                    try:
                        msg_data = json.loads(message)
                        if msg_data.get('type') == 'ping':
                            # 响应ping消息
                            await safe_send_text(websocket, json.dumps({"type": "ping", "timestamp": msg_data.get('timestamp')}))
                            continue
                    except json.JSONDecodeError:
                        logger.warning(f"收到无效JSON消息: {message}")
                        continue
                except:
                    # 如果不是文本消息，尝试接收音频数据
                    audio_bytes = await websocket.receive_bytes()
                    logger.debug(f"收到音频分片，长度: {len(audio_bytes)}")
                    
                    # 检查音频数据有效性
                    if len(audio_bytes) == 0:
                        logger.warning("收到空音频数据，跳过处理")
                        continue
                
                # 使用配置的音频大小过滤
                if len(audio_bytes) < config.min_audio_size:
                    logger.debug(f"音频数据过小，当前大小: {len(audio_bytes)}, 最小要求: {config.min_audio_size}，跳过处理")
                    continue
                
                logger.info(f"✅ 音频数据大小合适: {len(audio_bytes)} 字节，开始处理...")
                
                # 1. 异步转录（优化重试）
                t0 = time.time()
                text, error = await transcribe_audio_with_retry(client, audio_bytes)
                t1 = time.time()
                
                if error:
                    logger.error(error)
                    await safe_send_text(websocket, json.dumps({"error": error}))
                    continue
                
                if not text or len(text.strip()) < 2:
                    logger.debug(f"转录结果为空或过短: '{text}'，跳过此次处理")
                    await safe_send_text(websocket, json.dumps({"type": "transcription", "text": ""}))
                    continue
                
                logger.info(f"📝 转录成功: '{text}' (耗时: {t1-t0:.2f}s)")
                await safe_send_text(websocket, json.dumps({"type": "transcription", "text": text}))
                
                # 2. 优化的LLM+TTS流式处理
                t0 = time.time()
                success = await process_llm_stream_optimized(client, text, websocket)
                t1 = time.time()
                
                if success:
                    logger.info(f"LLM+TTS全流程耗时: {t1-t0:.2f}s")
                else:
                    logger.warning("LLM+TTS处理失败")
                    
        except WebSocketDisconnect:
            logger.info("WebSocket 连接已断开")
        except Exception as e:
            logger.error(f"WebSocket处理异常: {e}")
            try:
                await safe_send_text(websocket, json.dumps({"error": f"服务器内部错误: {str(e)}"}))
            except:
                pass  # 如果连接已断开，忽略发送错误
        finally:
            if websocket.client_state == WebSocketState.CONNECTED:
                try:
                    await websocket.close()
                except:
                    pass
            logger.info("WebSocket连接已清理") 