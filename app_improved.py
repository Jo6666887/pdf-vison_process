import streamlit as st
import os
import shutil
from pathlib import Path
import pdf2image
from PIL import Image
import concurrent.futures
from openai import OpenAI
import time
from datetime import datetime
import base64
import tkinter as tk
from tkinter import filedialog
import threading
import queue

# 页面配置
st.set_page_config(
    page_title="PDF智能解析工具",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 初始化session state
if 'processed_files' not in st.session_state:
    st.session_state.processed_files = []
if 'parsing_progress' not in st.session_state:
    st.session_state.parsing_progress = {}
if 'output_dir' not in st.session_state:
    st.session_state.output_dir = str(Path.home() / "Desktop" / "PDF解析结果")
if 'selected_folder' not in st.session_state:
    st.session_state.selected_folder = None

# 自定义CSS样式
st.markdown("""
<style>
    .stProgress > div > div > div > div {
        background-color: #4CAF50;
    }
    .upload-text {
        font-size: 16px;
        color: #555;
    }
    .success-message {
        padding: 10px;
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 5px;
        color: #155724;
    }
    .error-message {
        padding: 10px;
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        border-radius: 5px;
        color: #721c24;
    }
    .info-box {
        padding: 15px;
        background-color: #e3f2fd;
        border: 1px solid #bbdefb;
        border-radius: 5px;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

# 文件夹选择功能
def select_folder():
    """使用tkinter选择文件夹"""
    root = tk.Tk()
    root.withdraw()
    root.wm_attributes('-topmost', 1)
    folder_path = filedialog.askdirectory(
        title="选择输出目录",
        initialdir=st.session_state.output_dir
    )
    root.destroy()
    return folder_path

# 页面标题
st.title("📄 PDF智能解析工具")
st.markdown("---")

# 侧边栏配置
with st.sidebar:
    st.header("⚙️ 配置设置")
    
    # 输出目录选择
    st.subheader("📁 选择输出目录")
    col1, col2 = st.columns([3, 1])
    with col1:
        output_dir = st.text_input(
            "输出路径",
            value=st.session_state.output_dir,
            help="解析结果将保存到此目录"
        )
    with col2:
        if st.button("📂", key="browse_dir", help="浏览文件夹"):
            folder = select_folder()
            if folder:
                st.session_state.output_dir = folder
                st.rerun()
    
    # 更新输出目录
    if output_dir != st.session_state.output_dir:
        st.session_state.output_dir = output_dir
    
    # 显示当前输出目录
    st.info(f"📍 当前输出目录:\n{st.session_state.output_dir}")
    
    # API配置
    st.subheader("🔑 API配置")
    api_key = st.text_input(
        "ARK API Key",
        type="password",
        value=os.environ.get("ARK_API_KEY", "acdbc611-f206-416e-afaa-331d1fbcff88"),
        help="输入您的ARK API密钥"
    )
    
    if api_key:
        os.environ["ARK_API_KEY"] = api_key
    
    # 并发设置
    st.subheader("⚡ 性能设置")
    max_workers = st.slider(
        "并发客户端数",
        min_value=1,
        max_value=5,
        value=2,
        help="同时处理的页面数量"
    )
    
    # 高级设置
    with st.expander("🔧 高级设置"):
        dpi = st.slider(
            "PDF转图片DPI",
            min_value=100,
            max_value=400,
            value=200,
            step=50,
            help="DPI越高，图片质量越好，但文件越大"
        )
        
        timeout = st.number_input(
            "API超时时间（秒）",
            min_value=10,
            max_value=300,
            value=60,
            help="单个API调用的超时时间"
        )

# 主页面布局
col1, col2 = st.columns([1, 2])

with col1:
    st.header("📤 上传PDF文件")
    
    # 文件上传区域
    uploaded_files = st.file_uploader(
        "选择PDF文件（最多20个）",
        type=['pdf'],
        accept_multiple_files=True,
        help="支持同时上传多个PDF文件",
        key="pdf_uploader"
    )
    
    if uploaded_files:
        st.success(f"✅ 已选择 {len(uploaded_files)} 个文件")
        if len(uploaded_files) > 20:
            st.error("⚠️ 最多只能同时上传20个文件！")
            uploaded_files = uploaded_files[:20]
        
        # 显示文件列表
        with st.expander("查看文件列表"):
            for i, file in enumerate(uploaded_files):
                file_size = len(file.getvalue()) / 1024 / 1024  # MB
                st.text(f"{i+1}. {file.name} ({file_size:.2f} MB)")

with col2:
    st.header("🤖 AI解析设置")
    
    # 预设提示词
    preset_prompts = {
        "通用文档分析": """请详细分析这张图片的内容，包括：
1. 主要文本内容
2. 图表或表格信息
3. 关键数据和要点
4. 其他重要信息

请以结构化的方式输出分析结果。""",
        
        "发票识别": """请识别这张发票图片中的以下信息：
1. 发票类型和编号
2. 开票日期
3. 购买方和销售方信息
4. 商品或服务明细
5. 金额信息（含税额、不含税额、税额）
6. 备注信息

请以JSON格式输出识别结果。""",
        
        "合同分析": """请分析这份合同页面的内容，重点关注：
1. 合同主体信息
2. 关键条款内容
3. 权利义务说明
4. 金额和期限
5. 特殊约定事项

请按条目整理输出。""",
        
        "表格提取": """请提取图片中的表格数据：
1. 识别表格结构
2. 提取所有单元格内容
3. 保持原有的行列关系
4. 标注表头信息

请以Markdown表格格式输出。"""
    }
    
    # 提示词选择
    prompt_type = st.selectbox(
        "选择提示词模板",
        options=list(preset_prompts.keys()) + ["自定义"],
        help="选择预设模板或自定义输入"
    )
    
    # 根据选择显示提示词
    if prompt_type == "自定义":
        prompt = st.text_area(
            "输入解析提示词（Prompt）",
            value=preset_prompts["通用文档分析"],
            height=200,
            help="AI将根据您的提示词来解析每一页内容"
        )
    else:
        prompt = st.text_area(
            "输入解析提示词（Prompt）",
            value=preset_prompts[prompt_type],
            height=200,
            help="AI将根据您的提示词来解析每一页内容"
        )

# 处理按钮和进度显示区域
st.markdown("---")
col1, col2, col3 = st.columns([1, 2, 1])

with col2:
    if st.button("🚀 开始处理", type="primary", disabled=not uploaded_files, use_container_width=True):
        if not api_key:
            st.error("❌ 请先配置API Key！")
        else:
            # 创建输出目录
            Path(st.session_state.output_dir).mkdir(parents=True, exist_ok=True)
            process_pdfs(uploaded_files, prompt, max_workers, dpi, timeout)

# 处理函数
def process_pdfs(files, prompt, max_workers, dpi=200, timeout=60):
    """处理上传的PDF文件"""
    # 创建进度容器
    progress_container = st.container()
    
    with progress_container:
        total_progress = st.progress(0)
        status_text = st.empty()
        detail_text = st.empty()
        
        total_files = len(files)
        
        for idx, uploaded_file in enumerate(files):
            file_progress = (idx) / total_files
            total_progress.progress(file_progress)
            status_text.text(f"处理中: {uploaded_file.name} ({idx+1}/{total_files})")
            
            try:
                # 创建输出目录结构
                base_output_dir = Path(st.session_state.output_dir)
                file_output_dir = base_output_dir / uploaded_file.name.replace('.pdf', '')
                pdf_dir = file_output_dir / 'pdf'
                slices_dir = file_output_dir / 'slice-pics'
                summaries_dir = file_output_dir / 'summaries'
                
                # 创建必要的目录
                for dir_path in [file_output_dir, pdf_dir, slices_dir, summaries_dir]:
                    dir_path.mkdir(parents=True, exist_ok=True)
                
                # 保存原始PDF
                detail_text.text("💾 保存原始PDF...")
                pdf_path = pdf_dir / uploaded_file.name
                with open(pdf_path, 'wb') as f:
                    f.write(uploaded_file.getvalue())
                
                # 拆分PDF为图片
                detail_text.text("✂️ 拆分PDF页面...")
                images = split_pdf_to_images(pdf_path, slices_dir, dpi)
                
                if images:
                    st.success(f"✅ {uploaded_file.name} 拆分完成！共 {len(images)} 页")
                    
                    # 使用AI解析每一页
                    detail_text.text("🤖 AI解析中...")
                    
                    # 创建页面进度条
                    page_progress_bar = st.progress(0)
                    page_status = st.empty()
                    
                    success = parse_images_with_ai(
                        images, 
                        summaries_dir, 
                        prompt, 
                        max_workers, 
                        page_progress_bar, 
                        page_status,
                        uploaded_file.name,
                        timeout
                    )
                    
                    if success:
                        st.session_state.processed_files.append({
                            'name': uploaded_file.name,
                            'pages': len(images),
                            'output_dir': str(file_output_dir),
                            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        })
                else:
                    st.error(f"❌ {uploaded_file.name} 拆分失败")
                    
            except Exception as e:
                st.error(f"❌ 处理 {uploaded_file.name} 时出错: {str(e)}")
            
            # 更新总进度
            file_progress = (idx + 1) / total_files
            total_progress.progress(file_progress)
    
    # 完成处理
    st.balloons()
    st.success("🎉 所有文件处理完成！")
    
    # 显示结果摘要
    with st.expander("📊 处理结果摘要", expanded=True):
        st.info(f"📁 结果保存位置: {st.session_state.output_dir}")
        
        if st.session_state.processed_files:
            # 创建结果表格
            import pandas as pd
            df = pd.DataFrame(st.session_state.processed_files)
            st.dataframe(df, use_container_width=True)

def split_pdf_to_images(pdf_path, output_dir, dpi=200):
    """将PDF拆分为图片"""
    try:
        # 使用pdf2image将PDF转换为图片
        images = pdf2image.convert_from_path(
            pdf_path, 
            dpi=dpi,
            fmt='png',
            thread_count=2,
            use_cropbox=True
        )
        saved_images = []
        
        for i, image in enumerate(images):
            image_path = output_dir / f"{i+1}.png"
            image.save(image_path, "PNG", optimize=True)
            saved_images.append(image_path)
        
        return saved_images
    except Exception as e:
        st.error(f"PDF拆分失败: {str(e)}")
        return []

def parse_images_with_ai(image_paths, output_dir, prompt, max_workers, progress_bar, status_text, file_name, timeout=60):
    """使用AI并发解析图片"""
    total_pages = len(image_paths)
    completed = 0
    failed = 0
    
    # 创建结果锁
    lock = threading.Lock()
    
    # 创建OpenAI客户端
    def create_client():
        return OpenAI(
            base_url="https://ark.cn-beijing.volces.com/api/v3",
            api_key=os.environ.get("ARK_API_KEY"),
            timeout=timeout
        )
    
    def parse_single_image(image_path, page_num):
        """解析单张图片"""
        nonlocal completed, failed
        try:
            # 将图片转换为base64
            with open(image_path, "rb") as img_file:
                base64_image = base64.b64encode(img_file.read()).decode('utf-8')
            
            # 创建客户端
            client = create_client()
            
            # 调用API
            response = client.chat.completions.create(
                model="ep-20250425135316-55rdv",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{base64_image}"
                                },
                            },
                            {"type": "text", "text": prompt},
                        ],
                    }
                ],
                max_tokens=4096,
                temperature=0.7
            )
            
            # 保存结果
            result_path = output_dir / f"{page_num}.txt"
            with open(result_path, "w", encoding="utf-8") as f:
                f.write(f"=== 第 {page_num} 页解析结果 ===\n\n")
                f.write(response.choices[0].message.content)
                f.write(f"\n\n=== 解析时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===")
            
            with lock:
                completed += 1
                progress = completed / total_pages
                progress_bar.progress(progress)
                status_text.text(f"解析进度: {completed}/{total_pages} 页 (失败: {failed})")
            
            return True
            
        except Exception as e:
            with lock:
                failed += 1
                completed += 1
                progress = completed / total_pages
                progress_bar.progress(progress)
                status_text.text(f"解析进度: {completed}/{total_pages} 页 (失败: {failed})")
            
            # 保存错误信息
            error_path = output_dir / f"{page_num}_error.txt"
            with open(error_path, "w", encoding="utf-8") as f:
                f.write(f"页面 {page_num} 解析失败\n")
                f.write(f"错误信息: {str(e)}\n")
                f.write(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            return False
    
    # 使用线程池并发处理
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = []
        for i, image_path in enumerate(image_paths):
            future = executor.submit(parse_single_image, image_path, i+1)
            futures.append(future)
        
        # 等待所有任务完成
        results = [future.result() for future in concurrent.futures.as_completed(futures)]
    
    # 创建汇总文件
    summary_path = output_dir / "_summary.txt"
    with open(summary_path, "w", encoding="utf-8") as f:
        f.write(f"PDF解析汇总报告\n")
        f.write(f"="*50 + "\n")
        f.write(f"文件名: {file_name}\n")
        f.write(f"总页数: {total_pages}\n")
        f.write(f"成功解析: {completed - failed} 页\n")
        f.write(f"解析失败: {failed} 页\n")
        f.write(f"解析时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    return failed == 0

# 显示处理历史
if st.session_state.processed_files:
    st.markdown("---")
    st.header("📊 处理历史")
    
    # 添加清空历史按钮
    col1, col2 = st.columns([4, 1])
    with col2:
        if st.button("🗑️ 清空历史"):
            st.session_state.processed_files = []
            st.rerun()
    
    # 显示历史记录
    for idx, file_info in enumerate(reversed(st.session_state.processed_files)):
        with st.expander(f"📄 {file_info['name']} - {file_info['timestamp']}"):
            col1, col2 = st.columns(2)
            with col1:
                st.text(f"📑 页数: {file_info['pages']}")
            with col2:
                st.text(f"📁 输出位置: {file_info['output_dir']}")
            
            # 添加打开文件夹按钮
            if st.button(f"打开文件夹", key=f"open_{idx}"):
                os.system(f"open '{file_info['output_dir']}'")

# 页脚
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #888;'>
        <p>PDF智能解析工具 v1.0 | Powered by Streamlit & Vision AI</p>
    </div>
    """,
    unsafe_allow_html=True
)