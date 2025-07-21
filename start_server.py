#!/usr/bin/env python3
"""
10KV AI 实时语音对话系统 - 服务器启动脚本
"""

import os
import sys
import asyncio
from pathlib import Path

def check_environment():
    """检查环境配置"""
    print("🔍 检查环境配置...")
    
    # 检查.env文件
    if not os.path.exists('.env'):
        print("⚠️  未找到 .env 文件")
        print("📝 请复制 config.env.template 为 .env 并填入配置")
        print("   cp config.env.template .env")
        return False
    
    print("✅ 配置文件检查通过")
    return True

def check_dependencies():
    """检查依赖包"""
    print("📦 检查依赖包...")
    
    required_packages = [
        'fastapi', 'uvicorn', 'httpx', 'pydantic', 'dotenv'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"❌ 缺少依赖包: {', '.join(missing_packages)}")
        print("📝 请运行: pip install -r requirements.txt")
        return False
    
    print("✅ 依赖包检查通过")
    return True

def main():
    """主函数"""
    print("🚀 10KV AI 实时语音对话系统")
    print("=" * 50)
    
    # 检查环境
    if not check_environment():
        sys.exit(1)
    
    if not check_dependencies():
        sys.exit(1)
    
    print("\n🌟 启动服务器...")
    
    try:
        # 导入并启动服务
        from api.main import app
        from api.config import get_settings
        import uvicorn
        
        config = get_settings()
        print(f"🌐 服务器地址: http://{config.host}:{config.port}")
        print(f"📚 API 文档: http://{config.host}:{config.port}/docs")
        print(f"🔄 实时聊天: ws://{config.host}:{config.port}/api/v1/ws/realtime")
        print("\n按 Ctrl+C 停止服务器\n")
        
        uvicorn.run(
            app,
            host=config.host,
            port=config.port,
            log_level="info" if not config.debug else "debug",
            reload=config.debug
        )
        
    except KeyboardInterrupt:
        print("\n👋 服务器已停止")
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        print("💡 请检查配置和依赖是否正确安装")
        sys.exit(1)

if __name__ == "__main__":
    main() 