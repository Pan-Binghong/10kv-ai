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
        "model": "CosyVoice2-0.5B",
        "input": user_input,
        "voice": "中文女",
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
