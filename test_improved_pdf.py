#!/usr/bin/env python3
"""
测试改进后的PDF处理功能
"""
from pathlib import Path
import time
from utils import PDFProcessor

def test_improved_pdf_processing():
    print("🚀 测试改进后的PDF处理功能...")
    
    # 使用指定的PDF文件
    pdf_file = Path("05SJ918-7 传统特色小城镇住宅(北京地区).pdf")
    
    if not pdf_file.exists():
        print(f"❌ 文件不存在: {pdf_file}")
        return
    
    print(f"📄 测试文件: {pdf_file.name}")
    print(f"📊 文件大小: {pdf_file.stat().st_size / 1024 / 1024:.2f} MB")
    
    # 创建输出目录
    output_dir = Path("test_output_images")
    output_dir.mkdir(exist_ok=True)
    
    # 创建PDF处理器
    processor = PDFProcessor(dpi=150)
    
    # 定义回调函数
    def progress_callback(progress):
        bar_length = 30
        filled_length = int(bar_length * progress)
        bar = '█' * filled_length + '░' * (bar_length - filled_length)
        print(f"\r🔄 进度: [{bar}] {progress*100:.1f}%", end='', flush=True)
    
    def status_callback(status):
        print(f"\n📝 {status}")
    
    try:
        print("⏳ 开始测试改进后的PDF处理...")
        start_time = time.time()
        
        images = processor.split_pdf_to_images(
            pdf_file, 
            output_dir,
            progress_callback=progress_callback,
            status_callback=status_callback
        )
        
        end_time = time.time()
        print(f"\n✅ 处理完成！")
        print(f"⏰ 总耗时: {end_time - start_time:.2f} 秒")
        print(f"📷 生成图片: {len(images)} 张")
        
        if images:
            print(f"📁 输出目录: {output_dir.absolute()}")
            print(f"🖼️ 第一张图片: {images[0].name}")
        
        # 清理测试文件
        print("🧹 清理测试文件...")
        for img in images:
            if img.exists():
                img.unlink()
        if output_dir.exists() and not any(output_dir.iterdir()):
            output_dir.rmdir()
        print("✅ 清理完成")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_improved_pdf_processing() 