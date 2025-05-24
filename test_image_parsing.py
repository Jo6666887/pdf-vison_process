#!/usr/bin/env python3
"""
图片解析功能测试脚本
"""

from pathlib import Path
import base64
from utils import AIParser
from config import ARK_API_CONFIG, PRESET_PROMPTS

def test_image_parsing_feature():
    """测试图片解析功能"""
    print("🖼️ 图片解析功能测试")
    print("=" * 50)
    
    # 查找测试图片
    print("📷 查找测试图片...")
    
    # 查找桌面PDF解析结果中的图片
    desktop_results = Path.home() / "Desktop" / "PDF解析结果"
    test_image = None
    
    if desktop_results.exists():
        for pdf_folder in desktop_results.iterdir():
            if pdf_folder.is_dir():
                slice_pics = pdf_folder / "slice-pics"
                if slice_pics.exists():
                    images = list(slice_pics.glob("*.png"))
                    if images:
                        test_image = images[0]  # 使用第一张图片
                        break
    
    if not test_image:
        print("❌ 未找到测试图片")
        print("💡 请先运行PDF解析或上传图片到应用中")
        return False
    
    print(f"✅ 使用测试图片: {test_image}")
    
    # 测试AI解析
    api_key = ARK_API_CONFIG["default_api_key"]
    if not api_key:
        print("❌ 未配置API密钥")
        return False
    
    print("🤖 测试AI图片解析...")
    
    try:
        # 创建AI解析器
        ai_parser = AIParser(api_key=api_key, timeout=60)
        
        # 读取图片并转换为base64
        with open(test_image, "rb") as img_file:
            base64_image = base64.b64encode(img_file.read()).decode('utf-8')
        
        # 使用通用文档分析提示词
        prompt = PRESET_PROMPTS["通用文档分析"]
        
        # 构建消息
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
                        "text": f"这是测试图片。{prompt}"
                    },
                ],
            }
        ]
        
        # 调用API
        client = ai_parser.create_client()
        response = client.chat.completions.create(
            model=ai_parser.model,
            messages=messages,
            max_tokens=2000,
            temperature=0.7,
            top_p=0.9
        )
        
        result = response.choices[0].message.content
        
        print("✅ 图片解析成功！")
        print("\n📝 解析结果预览:")
        print("-" * 40)
        print(result[:300] + "..." if len(result) > 300 else result)
        print("-" * 40)
        
        return True
        
    except Exception as e:
        print(f"❌ 图片解析失败: {e}")
        return False

def show_feature_instructions():
    """显示新功能使用说明"""
    print("\n" + "=" * 60)
    print("🎉 PDF智能解析工具 v2.1 新功能说明")
    print("=" * 60)
    
    print("\n📄 更新内容:")
    print("1. ✅ 移除文件夹选择按钮 (解决tkinter错误)")
    print("2. ✅ 添加图片智能解析功能")
    print("3. ✅ 实时解析结果显示")
    print("4. ✅ 批量解析和保存功能")
    
    print("\n🖼️ 图片解析功能使用方法:")
    print("1. 访问: http://localhost:8501")
    print("2. 点击 '🖼️ 图片智能解析' 选项卡")
    print("3. 上传图片文件 (支持 PNG、JPG、JPEG、GIF、BMP)")
    print("4. 选择或自定义解析提示词")
    print("5. 点击 '🔍 解析选中' 或 '🚀 批量解析'")
    print("6. 查看实时解析结果")
    print("7. 使用 '💾 保存结果' 批量导出")
    
    print("\n💡 特色功能:")
    print("• 无上传数量限制")
    print("• 实时结果预览")
    print("• 提示词实时调试")
    print("• 批量处理和保存")
    print("• 选项卡式界面")
    
    print("\n📁 快速目录设置:")
    print("• 🏠 设为桌面: 保存到桌面/PDF解析结果")
    print("• 📂 设为当前: 保存到项目目录/PDF解析结果")

if __name__ == "__main__":
    # 测试图片解析功能
    success = test_image_parsing_feature()
    
    # 显示功能说明
    show_feature_instructions()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 图片解析功能测试通过！")
        print("🚀 新版本应用已就绪，请在浏览器中体验")
    else:
        print("⚠️ 图片解析功能测试失败，但应用已更新")
        print("💡 可以直接在应用中上传图片进行测试")
    print("=" * 60) 