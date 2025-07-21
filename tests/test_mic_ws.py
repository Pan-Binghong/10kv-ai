import asyncio
import websockets
import sounddevice as sd
import numpy as np
import io
import wave
import queue

SAMPLE_RATE = 16000
CHANNELS = 1
CHUNK_DURATION = 1
CHUNK_SIZE = SAMPLE_RATE * CHUNK_DURATION

def pcm_to_wav_bytes(pcm_data, sample_rate, channels):
    buf = io.BytesIO()
    wf = wave.open(buf, 'wb')
    wf.setnchannels(channels)
    wf.setsampwidth(2)
    wf.setframerate(sample_rate)
    wf.writeframes(pcm_data)
    wf.close()
    return buf.getvalue()

async def mic_stream():
    uri = "ws://127.0.0.1:8000/ws/realtime"
    audio_queue = queue.Queue()

    def callback(indata, frames, time, status):
        pcm = (indata * 32767).astype(np.int16).tobytes()
        wav_bytes = pcm_to_wav_bytes(pcm, SAMPLE_RATE, CHANNELS)
        audio_queue.put(wav_bytes)

    stream = sd.InputStream(samplerate=SAMPLE_RATE, channels=CHANNELS, dtype='float32',
                            blocksize=CHUNK_SIZE, callback=callback)
    with stream, websockets.connect(uri, max_size=10*1024*1024) as websocket:
        print("正在录音并发送到WebSocket，按Ctrl+C停止...")
        loop = asyncio.get_event_loop()
        async def sender():
            while True:
                wav_bytes = await loop.run_in_executor(None, audio_queue.get)
                await websocket.send(wav_bytes)
        async def receiver():
            while True:
                msg = await websocket.recv()
                if isinstance(msg, bytes):
                    print("收到TTS音频流，长度：", len(msg))
                    with open("result_tts.wav", "wb") as f:
                        f.write(msg)
                else:
                    print("收到文本消息：", msg)
        await asyncio.gather(sender(), receiver())

asyncio.run(mic_stream())