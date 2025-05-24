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
</style>
""", unsafe_allow_html=True)

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
        if st.button("浏览", key="browse_dir"):
            # 这里可以添加文件夹选择对话框
            pass
    
    # 更新输出目录
    if output_dir != st.session_state.output_dir:
        st.session_state.output_dir = output_dir
    
    # API配置
    st.subheader("🔑 API配置")
    api_key = st.text_input(
        "ARK API Key",
        type="password",
        value=os.environ.get("ARK_API_KEY", ""),
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

# 主页面布局
col1, col2 = st.columns([1, 2])

with col1:
    st.header("📤 上传PDF文件")
    uploaded_files = st.file_uploader(
        "选择PDF文件（最多20个）",
        type=['pdf'],
        accept_multiple_files=True,
        help="支持同时上传多个PDF文件",
        key="pdf_uploader"
    )
    
    if uploaded_files:
        st.info(f"已选择 {len(uploaded_files)} 个文件")
        if len(uploaded_files) > 20:
            st.error("最多只能同时上传20个文件！")
            uploaded_files = uploaded_files[:20]

with col2:
    st.header("🤖 AI解析设置")
    
    # Prompt输入
    default_prompt = """请详细分析这张图片的内容，包括：
1. 主要文本内容
2. 图表或表格信息
3. 关键数据和要点
4. 其他重要信息

请以结构化的方式输出分析结果。"""
    
    prompt = st.text_area(
        "输入解析提示词（Prompt）",
        value=default_prompt,
        height=150,
        help="AI将根据您的提示词来解析每一页内容"
    )

# 处理按钮
if st.button("🚀 开始处理", type="primary", disabled=not uploaded_files):
    if not api_key:
        st.error("请先配置API Key！")
    else:
        process_pdfs(uploaded_files, prompt, max_workers)

# 处理函数
def process_pdfs(files, prompt, max_workers):
    """处理上传的PDF文件"""
    progress_placeholder = st.empty()
    status_placeholder = st.empty()
    
    for idx, uploaded_file in enumerate(files):
        with st.spinner(f"正在处理 {uploaded_file.name} ({idx+1}/{len(files)})..."):
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
            pdf_path = pdf_dir / uploaded_file.name
            with open(pdf_path, 'wb') as f:
                f.write(uploaded_file.getvalue())
            
            # 拆分PDF为图片
            status_placeholder.info(f"📄 正在拆分 {uploaded_file.name}...")
            images = split_pdf_to_images(pdf_path, slices_dir)
            
            if images:
                status_placeholder.success(f"✅ {uploaded_file.name} 拆分完成！共 {len(images)} 页")
                time.sleep(1)
                
                # 使用AI解析每一页
                status_placeholder.info(f"🤖 正在使用AI解析 {uploaded_file.name}...")
                parse_images_with_ai(images, summaries_dir, prompt, max_workers, progress_placeholder, uploaded_file.name)
                
                st.session_state.processed_files.append(uploaded_file.name)
    
    st.balloons()
    st.success("🎉 所有文件处理完成！")
    st.info(f"结果已保存到: {st.session_state.output_dir}")

def split_pdf_to_images(pdf_path, output_dir):
    """将PDF拆分为图片"""
    try:
        # 使用pdf2image将PDF转换为图片
        images = pdf2image.convert_from_path(pdf_path, dpi=200)
        saved_images = []
        
        for i, image in enumerate(images):
            image_path = output_dir / f"{i+1}.png"
            image.save(image_path, "PNG")
            saved_images.append(image_path)
        
        return saved_images
    except Exception as e:
        st.error(f"PDF拆分失败: {str(e)}")
        return []

def parse_images_with_ai(image_paths, output_dir, prompt, max_workers, progress_placeholder, file_name):
    """使用AI并发解析图片"""
    total_pages = len(image_paths)
    completed = 0
    
    # 创建OpenAI客户端
    def create_client():
        return OpenAI(
            base_url="https://ark.cn-beijing.volces.com/api/v3",
            api_key=os.environ.get("ARK_API_KEY"),
        )
    
    def parse_single_image(image_path, page_num):
        """解析单张图片"""
        nonlocal completed
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
            )
            
            # 保存结果
            result_path = output_dir / f"{page_num}.txt"
            with open(result_path, "w", encoding="utf-8") as f:
                f.write(response.choices[0].message.content)
            
            completed += 1
            progress = completed / total_pages
            progress_placeholder.progress(progress, f"解析进度: {completed}/{total_pages} 页 ({file_name})")
            
            return True
        except Exception as e:
            st.error(f"页面 {page_num} 解析失败: {str(e)}")
            return False
    
    # 使用线程池并发处理
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = []
        for i, image_path in enumerate(image_paths):
            future = executor.submit(parse_single_image, image_path, i+1)
            futures.append(future)
        
        # 等待所有任务完成
        concurrent.futures.wait(futures)

# 显示已处理的文件
if st.session_state.processed_files:
    st.markdown("---")
    st.header("📊 处理历史")
    for file in st.session_state.processed_files:
        st.success(f"✅ {file}")