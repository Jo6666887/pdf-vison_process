#!/usr/bin/env python3
"""
批量AI解析测试脚本 - 测试已拆分PDF的AI解析功能
"""

from pathlib import Path
from utils import AIParser
from config import ARK_API_CONFIG, PRESET_PROMPTS

def test_batch_ai_parsing():
    """测试批量AI解析功能"""
    print("🤖 批量AI解析测试")
    print("=" * 50)
    
    # 查找已拆分的PDF图片
    desktop_results = Path.home() / "Desktop" / "PDF解析结果"
    
    if not desktop_results.exists():
        print("❌ 未找到PDF解析结果目录")
        return False
    
    # 查找有图片但没有解析结果的PDF
    pdf_folders = [d for d in desktop_results.iterdir() if d.is_dir()]
    
    target_folder = None
    for pdf_folder in pdf_folders:
        slice_pics = pdf_folder / "slice-pics"
        summaries = pdf_folder / "summaries"
        
        if slice_pics.exists() and len(list(slice_pics.glob("*.png"))) > 0:
            if not summaries.exists() or len(list(summaries.glob("*.txt"))) == 0:
                target_folder = pdf_folder
                break
    
    if not target_folder:
        print("❌ 未找到需要AI解析的PDF文件夹")
        return False
    
    print(f"📁 目标文件夹: {target_folder.name}")
    
    # 获取图片列表
    slice_pics_dir = target_folder / "slice-pics"
    images = sorted(list(slice_pics_dir.glob("*.png")), key=lambda x: int(x.stem))
    
    print(f"📷 找到 {len(images)} 张图片")
    
    # 创建AI解析器
    api_key = ARK_API_CONFIG["default_api_key"]
    ai_parser = AIParser(api_key=api_key, timeout=60)
    
    # 创建输出目录
    summaries_dir = target_folder / "summaries"
    summaries_dir.mkdir(exist_ok=True)
    
    # 使用通用文档分析提示词
    prompt = PRESET_PROMPTS["通用文档分析"]
    
    print(f"📝 使用提示词: {prompt[:50]}...")
    print("\n🚀 开始批量解析...")
    
    # 定义进度回调
    def progress_callback(progress):
        bar_length = 30
        filled_length = int(bar_length * progress)
        bar = '█' * filled_length + '░' * (bar_length - filled_length)
        print(f"\r🔄 进度: [{bar}] {progress*100:.1f}%", end='', flush=True)
    
    def status_callback(status):
        print(f"\n📝 {status}")
    
    try:
        # 只处理前3张图片进行测试
        test_images = images[:3]
        print(f"🧪 测试模式：只处理前 {len(test_images)} 张图片")
        
        result = ai_parser.parse_images_batch(
            test_images,
            summaries_dir,
            prompt,
            max_workers=2,  # 使用较少的并发数
            progress_callback=progress_callback,
            status_callback=status_callback
        )
        
        print(f"\n✅ 测试完成！")
        print(f"📊 总页数: {result['total_pages']}")
        print(f"✅ 成功: {result['successful']}")
        print(f"❌ 失败: {result['failed']}")
        
        # 显示解析结果示例
        if result['successful'] > 0:
            print("\n📄 解析结果示例:")
            print("-" * 30)
            for page_num, page_result in result['results'].items():
                if page_result['success']:
                    content = page_result['content'][:200] + "..." if len(page_result['content']) > 200 else page_result['content']
                    print(f"第{page_num}页: {content}")
                    break
            print("-" * 30)
        
        return result['successful'] > 0
        
    except Exception as e:
        print(f"\n❌ 批量解析失败: {e}")
        return False

if __name__ == "__main__":
    success = test_batch_ai_parsing()
    print("\n" + "=" * 50)
    if success:
        print("🎉 批量AI解析测试成功！")
        print("💡 现在可以在Streamlit中进行完整的AI解析")
    else:
        print("⚠️ 批量AI解析测试失败，请检查配置") 