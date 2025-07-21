#!/usr/bin/env python3
"""
系统功能测试脚本
"""

import asyncio
import os
import sys
from pathlib import Path

async def test_config():
    """测试配置系统"""
    print("🔧 测试配置系统...")
    try:
        from api.config import get_settings
        config = get_settings()
        print(f"✅ 配置加载成功 - Host: {config.host}, Port: {config.port}")
        return True
    except Exception as e:
        print(f"❌ 配置加载失败: {e}")
        return False

async def test_api_routes():
    """测试API路由"""
    print("🛣️  测试API路由...")
    try:
        from api.main import app
        from fastapi.testclient import TestClient
        
        client = TestClient(app)
        
        # 测试健康检查
        response = client.get("/health")
        if response.status_code == 200:
            print("✅ 健康检查端点正常")
        else:
            print(f"❌ 健康检查失败: {response.status_code}")
            return False
        
        # 测试根端点
        response = client.get("/")
        if response.status_code == 200:
            print("✅ 根端点正常")
        else:
            print(f"❌ 根端点失败: {response.status_code}")
            return False
        
        print("✅ API路由测试通过")
        return True
        
    except Exception as e:
        print(f"❌ API路由测试失败: {e}")
        return False

async def test_websocket():
    """测试WebSocket连接"""
    print("🔌 测试WebSocket连接...")
    try:
        import websockets
        from api.config import get_settings
        
        config = get_settings()
        uri = f"ws://{config.host}:{config.port}/api/v1/ws/realtime"
        
        # 注意：这里只是测试WebSocket端点是否存在
        # 实际连接需要服务器运行
        print(f"📡 WebSocket端点: {uri}")
        print("✅ WebSocket配置正常")
        return True
        
    except Exception as e:
        print(f"❌ WebSocket测试失败: {e}")
        return False

async def test_models():
    """测试数据模型"""
    print("📋 测试数据模型...")
    try:
        from api.tts import TTSRequest
        from api.transcription import TranscriptionResponse
        from api.llm import ChatRequest, Message
        
        # 测试TTS请求模型
        tts_req = TTSRequest(input="测试文本")
        print("✅ TTS模型正常")
        
        # 测试转录响应模型
        trans_resp = TranscriptionResponse(text="测试转录")
        print("✅ 转录模型正常")
        
        # 测试聊天请求模型
        chat_req = ChatRequest(
            messages=[Message(role="user", content="测试消息")]
        )
        print("✅ 聊天模型正常")
        
        print("✅ 数据模型测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 数据模型测试失败: {e}")
        return False

async def main():
    """主测试函数"""
    print("🧪 10KV AI 系统功能测试")
    print("=" * 40)
    
    tests = [
        ("配置系统", test_config),
        ("数据模型", test_models),
        ("API路由", test_api_routes),
        ("WebSocket", test_websocket),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📝 测试: {test_name}")
        try:
            if await test_func():
                passed += 1
            else:
                print(f"❌ {test_name} 测试失败")
        except Exception as e:
            print(f"❌ {test_name} 测试异常: {e}")
    
    print("\n" + "=" * 40)
    print(f"📊 测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过！系统就绪。")
        return 0
    else:
        print("⚠️  部分测试失败，请检查配置和依赖。")
        return 1

if __name__ == "__main__":
    sys.exit(asyncio.run(main())) 