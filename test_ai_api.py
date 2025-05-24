#!/usr/bin/env python3
"""
AI API测试脚本 - 验证ARK API连接和解析功能
"""

import base64
from pathlib import Path
from openai import OpenAI
from config import ARK_API_CONFIG

def test_ai_api():
    """测试AI API连接和功能"""
    print("🤖 AI API连接测试")
    print("=" * 50)
    
    # 获取API配置
    api_key = ARK_API_CONFIG.get("default_api_key")
    base_url = ARK_API_CONFIG.get("base_url")
    model = ARK_API_CONFIG.get("model")
    
    print(f"🔑 API密钥: {api_key[:20]}..." if api_key else "❌ 未设置API密钥")
    print(f"🌐 API地址: {base_url}")
    print(f"🎯 模型名称: {model}")
    
    if not api_key:
        print("❌ 请在config.py中配置API密钥")
        return False
    
    # 查找测试图片
    print("\n📷 查找测试图片...")
    image_dirs = [
        Path("slice-pics"),
        Path("test_output_images"),
        Path.home() / "Desktop" / "PDF解析结果"
    ]
    
    # 查找任何PDF输出目录中的图片
    for pdf_dir in Path(".").glob("*/slice-pics"):
        image_dirs.append(pdf_dir)
    
    # 查找桌面PDF解析结果目录中的slice-pics
    desktop_result_dir = Path.home() / "Desktop" / "PDF解析结果"
    if desktop_result_dir.exists():
        for pdf_folder in desktop_result_dir.iterdir():
            if pdf_folder.is_dir():
                slice_pics_dir = pdf_folder / "slice-pics"
                if slice_pics_dir.exists():
                    image_dirs.append(slice_pics_dir)
    
    test_image = None
    for img_dir in image_dirs:
        if img_dir.exists():
            images = list(img_dir.glob("*.png"))
            if images:
                test_image = images[0]  # 使用第一张图片
                break
    
    if not test_image:
        print("❌ 未找到测试图片，请先运行PDF拆分")
        return False
    
    print(f"✅ 使用测试图片: {test_image}")
    
    # 创建AI客户端
    try:
        client = OpenAI(
            base_url=base_url,
            api_key=api_key,
            timeout=30
        )
        print("✅ AI客户端创建成功")
    except Exception as e:
        print(f"❌ AI客户端创建失败: {e}")
        return False
    
    # 转换图片为base64
    try:
        with open(test_image, "rb") as img_file:
            base64_image = base64.b64encode(img_file.read()).decode('utf-8')
        print("✅ 图片转换为base64成功")
    except Exception as e:
        print(f"❌ 图片转换失败: {e}")
        return False
    
    # 测试AI解析
    print("\n🧠 开始AI解析测试...")
    try:
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{base64_image}"
                        },
                    },
                    {
                        "type": "text", 
                        "text": "请简要描述这张图片的内容，包括文档类型、主要信息和结构。"
                    },
                ],
            }
        ]
        
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=1000,
            temperature=0.7,
            top_p=0.9
        )
        
        print("✅ AI解析成功！")
        print("\n📝 解析结果:")
        print("-" * 30)
        print(response.choices[0].message.content)
        print("-" * 30)
        
        return True
        
    except Exception as e:
        print(f"❌ AI解析失败: {e}")
        print(f"🔧 错误类型: {type(e).__name__}")
        
        # 打印详细错误信息
        if hasattr(e, 'response'):
            print(f"📊 HTTP状态码: {e.response.status_code if hasattr(e.response, 'status_code') else '未知'}")
        
        return False

if __name__ == "__main__":
    success = test_ai_api()
    print("\n" + "=" * 50)
    if success:
        print("🎉 AI API测试通过！可以正常使用")
    else:
        print("⚠️ AI API测试失败，请检查配置和网络连接") 