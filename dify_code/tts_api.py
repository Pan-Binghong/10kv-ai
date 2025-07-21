import requests
import wave
import io
import base64

def main(user_input: str) -> dict:
    url = "http://221.181.122.58:23006/v1/audio/speech"
    headers = {
        "Content-Type": "application/octet-stream"
    }
    payload = {
        "model": "ChatTTS",
        "input": user_input,
        "voice": "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",
        "speed": 0.9,
        "stream": True
    }

    try:
        response = requests.post(url, json=payload, headers=headers, stream=True, timeout=60)
        if response.status_code == 200:
            audio_bytes = b""
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    audio_bytes += chunk
            # 检查是否为WAV
            if audio_bytes[:4] == b'RIFF':
                wav_bytes = audio_bytes
                msg = "音频为标准WAV格式"
            else:
                # 假设为PCM，封装为WAV
                sample_rate = 24000
                sample_width = 2
                channels = 1
                wav_buffer = io.BytesIO()
                with wave.open(wav_buffer, "wb") as wavfile:
                    wavfile.setnchannels(channels)
                    wavfile.setsampwidth(sample_width)
                    wavfile.setframerate(sample_rate)
                    wavfile.writeframes(audio_bytes)
                wav_bytes = wav_buffer.getvalue()
                msg = "音频为PCM格式，已自动封装为WAV"
            # 返回base64字符串
            audio_b64 = base64.b64encode(wav_bytes).decode("utf-8")
            return {
                "status": "success",
                "message": msg,
                "audio_base64": audio_b64
            }
        else:
            return {
                "status": "error",
                "message": f"TTS服务返回错误: {response.status_code}",
                "audio_base64": ""
            }
    except Exception as e:
        return {
            "status": "error",
            "message": f"请求TTS服务异常: {str(e)}",
            "audio_base64": ""
        }