#!/usr/bin/env python3
"""
测试PDF拆分功能
"""
import pdf2image
from pathlib import Path
import time

def test_pdf_split():
    print("🔍 开始测试PDF拆分功能...")
    
    # 使用指定的PDF文件
    pdf_file = Path("05SJ918-7 传统特色小城镇住宅(北京地区).pdf")
    
    if not pdf_file.exists():
        print(f"❌ 文件不存在: {pdf_file}")
        return
    
    print(f"📄 测试文件: {pdf_file.name}")
    print(f"📊 文件大小: {pdf_file.stat().st_size / 1024 / 1024:.2f} MB")
    
    try:
        print("⏳ 开始转换所有页面...")
        start_time = time.time()
        
        # 转换所有页面
        images = pdf2image.convert_from_path(
            pdf_file, 
            dpi=150  # 降低DPI提高速度
        )
        
        end_time = time.time()
        print(f"✅ 转换成功！耗时: {end_time - start_time:.2f} 秒")
        print(f"📷 生成图片数量: {len(images)}")
        
        if images:
            test_img = images[0]
            print(f"🖼️ 第一页图片尺寸: {test_img.size}")
            print(f"🎨 图片模式: {test_img.mode}")
        
        # 测试保存功能
        print("💾 测试保存第一页...")
        if images:
            test_output = Path("test_output.png")
            images[0].save(test_output)
            print(f"✅ 保存成功: {test_output}")
            
            # 清理测试文件
            if test_output.exists():
                test_output.unlink()
                print("🧹 清理测试文件完成")
        
    except Exception as e:
        print(f"❌ 转换失败: {str(e)}")
        print(f"🔧 错误类型: {type(e).__name__}")
        import traceback
        print(f"📍 详细错误信息:")
        traceback.print_exc()

if __name__ == "__main__":
    test_pdf_split() 