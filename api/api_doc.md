## 接口说明
实时语音对话后端系统, 使用FastAPI构建

`uvicorn main:app --reload`

### LLM
大模型调用代码, 以及接口的输入输出
```python
import requests
import json

url = "https://api.chatanywhere.tech/v1/chat/completions"

payload = json.dumps({
   "model": "gpt-4o-ca",
   "prompt": "Say this is a test",
   "max_tokens": 7,
   "temperature": 0,
   "top_p": 1,
   "n": 1,
   "stream": False,
   "logprobs": None,
   "stop": "\n"
})
headers = {
   'Authorization': 'Bearer your_api_key_here',
   'Content-Type': 'application/json'
}

response = requests.request("POST", url, headers=headers, data=payload)

print(response.text)
```

- 输入
{
    "model": "gpt-4o-ca",
    "messages": [
      {
        "role": "system",
        "content": "You are a helpful assistant."
      },
      {
        "role": "user",
        "content": "你好"
      }
    ]
  }

- 输出
{
    "id": "chatcmpl-BtpEt21FjPvbBN7jP9UAhcrnhiufh",
    "choices": [
        {
            "index": 0,
            "message": {
                "role": "assistant",
                "content": "你好！有什么我可以帮助你的吗？",
                "annotations": []
            },
            "logprobs": null,
            "finish_reason": "stop"
        }
    ],
    "created": 1752644703,
    "model": "gpt-4o-2024-08-06",
    "object": "chat.completion",
    "usage": {
        "prompt_tokens": 18,
        "completion_tokens": 10,
        "total_tokens": 28,
        "completion_tokens_details": {
            "audio_tokens": 0,
            "reasoning_tokens": 0
        },
        "prompt_tokens_details": {
            "audio_tokens": 0,
            "cached_tokens": 0
        }
    },
    "system_fingerprint": "fp_ee1d74bde0"
}{
    "id": "chatcmpl-BtpEt21FjPvbBN7jP9UAhcrnhiufh",
    "choices": [
        {
            "index": 0,
            "message": {
                "role": "assistant",
                "content": "你好！有什么我可以帮助你的吗？",
                "annotations": []
            },
            "logprobs": null,
            "finish_reason": "stop"
        }
    ],
    "created": 1752644703,
    "model": "gpt-4o-2024-08-06",
    "object": "chat.completion",
    "usage": {
        "prompt_tokens": 18,
        "completion_tokens": 10,
        "total_tokens": 28,
        "completion_tokens_details": {
            "audio_tokens": 0,
            "reasoning_tokens": 0
        },
        "prompt_tokens_details": {
            "audio_tokens": 0,
            "cached_tokens": 0
        }
    },
    "system_fingerprint": "fp_ee1d74bde0"
}


### 转录
语音转录调用的代码, 以及接口的输入输出
```python
import openai

client = openai.Client(
    api_key="cannot be empty",
    base_url="http://http://221.181.122.58:23006/v1"
)
with open("speech.mp3", "rb") as audio_file:
    client.audio.transcriptions.create(
        model=<MODEL_UID>,
        file=audio_file,
    )
```

- 输入
{
    "file":"二进制文件",
    "model":"SenseVoiceSmall"  
}

- 输出
{
    "text": "hello,大家好，欢迎来到我们的节目。今天我们要分享一个非常特别的消息。😊"
}


### TTS
文字转语音调用的代码, 以及接口的输入输出
```python
import openai

client = openai.Client(
    api_key="cannot be empty",
    base_url="http://http://221.181.122.58:23006/v1"
)
client.audio.speech.create(
    model=<MODEL_UID>,
    input=<The text to generate audio for>,
    voice="echo",
)
```

- 输入
{
"model":"ChatTTS",
"input":"你是谁, 我可以用你做什么?",
"voice":"AAAAANGeZ1UCAAAAAgAAAA8AAAAAAAAAAAAAAAAA0A0AAGFyY2hpdmUvdmVyc2lvblBLAQIAAAAACAgAAAAAAABOREdMKAAAACgAAAAeAAAAAAAAAAAAAAAAAFIOAABhcmNoaXZlLy5kYXRhL3NlcmlhbGl6YXRpb25faWRQSwYGLAAAAAAAAAAeAy0AAAAAAAAAAAAFAAAAAAAAAAUAAAAAAAAAQgEAAAAAAAD4DgAAAAAAAFBLBgcAAAAAOhAAAAAAAAABAAAAUEsFBgAAAAAFAAUAQgEAAPgOAAAAAA=="
}

- 输出
application/octet-stream
file
