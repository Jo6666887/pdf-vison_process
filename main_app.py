"""
PDF智能解析工具 - 主应用
"""

import streamlit as st
import os
import time
from pathlib import Path
from datetime import datetime
import pandas as pd
import base64
from PIL import Image
import io

# 导入自定义模块
from config import (
    UI_CONFIG, FILE_CONFIG, CONCURRENCY_CONFIG, OUTPUT_CONFIG, 
    PRESET_PROMPTS, ERROR_MESSAGES, SUCCESS_MESSAGES, ARK_API_CONFIG
)
from utils import PDFProcessor, AIParser, FileManager, ProgressTracker, validate_api_key, format_file_size

# 页面配置
st.set_page_config(
    page_title=UI_CONFIG["page_title"],
    page_icon=UI_CONFIG["page_icon"],
    layout=UI_CONFIG["layout"],
    initial_sidebar_state=UI_CONFIG["sidebar_state"]
)

# 初始化session state
def init_session_state():
    """初始化会话状态"""
    defaults = {
        'processed_files': [],
        'parsing_progress': {},
        'output_dir': OUTPUT_CONFIG["default_output_dir"],
        'selected_folder': None,
        'processing': False
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_session_state()

# 自定义CSS样式
def load_custom_css():
    """加载自定义CSS样式"""
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
        .metric-card {
            background-color: #f8f9fa;
            padding: 15px;
            border-radius: 10px;
            border: 1px solid #dee2e6;
            text-align: center;
        }
        .file-item {
            background-color: #ffffff;
            padding: 10px;
            border-radius: 5px;
            border: 1px solid #e0e0e0;
            margin: 5px 0;
        }
        .image-preview {
            border: 2px solid #e0e0e0;
            border-radius: 10px;
            padding: 10px;
            background-color: #f8f9fa;
        }
        .result-container {
            background-color: #ffffff;
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            padding: 15px;
            margin: 10px 0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .prompt-editor {
            border: 1px solid #ccc;
            border-radius: 5px;
            background-color: #f9f9f9;
        }
        .tab-content {
            padding: 20px 0;
        }
        .image-info {
            font-size: 12px;
            color: #666;
            background-color: #f0f0f0;
            padding: 5px 10px;
            border-radius: 3px;
            margin-top: 5px;
        }
    </style>
    """, unsafe_allow_html=True)

load_custom_css()

# 页面标题和介绍
def render_header():
    """渲染页面头部"""
    st.title("📄 PDF智能解析工具")
    st.markdown("""
    <div class="info-box">
        <h4>🚀 功能特点</h4>
        <ul>
            <li>📄 支持批量上传PDF文件（最多20个）</li>
            <li>🖼️ 自动拆分PDF为高清图片</li>
            <li>🤖 AI智能解析每页内容</li>
            <li>⚡ 多线程并发处理，提高效率</li>
            <li>📊 实时进度显示</li>
            <li>📁 结构化存储结果</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("---")

# 侧边栏配置
def render_sidebar():
    """渲染侧边栏"""
    with st.sidebar:
        st.header("⚙️ 配置设置")
        
        # 输出目录选择
        st.subheader("📁 输出目录")
        output_dir = st.text_input(
            "输出路径",
            value=st.session_state.output_dir,
            help="解析结果将保存到此目录",
            key="output_dir_input"
        )
        
        # 更新输出目录
        if output_dir != st.session_state.output_dir:
            st.session_state.output_dir = output_dir
        
        # 显示当前输出目录
        st.info(f"📍 当前输出目录:\n{st.session_state.output_dir}")
        
        # 快速设置常用目录
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🏠 设为桌面", key="set_desktop"):
                st.session_state.output_dir = str(Path.home() / "Desktop" / "PDF解析结果")
                st.rerun()
        with col2:
            if st.button("📂 设为当前", key="set_current"):
                st.session_state.output_dir = str(Path.cwd() / "PDF解析结果")
                st.rerun()
        
        # API配置
        st.subheader("🔑 API配置")
        api_key = st.text_input(
            "ARK API Key",
            type="password",
            value=os.environ.get("ARK_API_KEY", ARK_API_CONFIG["default_api_key"]),
            help="输入您的ARK API密钥"
        )
        
        if api_key:
            os.environ["ARK_API_KEY"] = api_key
        
        # 验证API密钥
        if validate_api_key(api_key):
            st.success("✅ API密钥格式正确")
        else:
            st.warning("⚠️ 请输入有效的API密钥")
        
        # 性能设置
        st.subheader("⚡ 性能设置")
        max_workers = st.slider(
            "并发客户端数",
            min_value=1,
            max_value=CONCURRENCY_CONFIG["max_workers"],
            value=CONCURRENCY_CONFIG["default_workers"],
            help="同时处理的页面数量"
        )
        
        # 高级设置
        with st.expander("🔧 高级设置"):
            dpi = st.slider(
                "PDF转图片DPI",
                min_value=FILE_CONFIG["min_dpi"],
                max_value=FILE_CONFIG["max_dpi"],
                value=FILE_CONFIG["default_dpi"],
                step=50,
                help="DPI越高，图片质量越好，但文件越大"
            )
            
            timeout = st.number_input(
                "API超时时间（秒）",
                min_value=10,
                max_value=CONCURRENCY_CONFIG["max_timeout"],
                value=CONCURRENCY_CONFIG["default_timeout"],
                help="单个API调用的超时时间"
            )
            
            # 显示系统信息
            if st.button("🖥️ 系统信息"):
                try:
                    from utils import get_system_info
                    info = get_system_info()
                    st.json(info)
                except Exception as e:
                    st.error(f"获取系统信息失败: {str(e)}")
    
    return api_key, max_workers, dpi, timeout

# 文件上传区域
def render_file_upload():
    """渲染文件上传区域"""
    st.header("📤 上传PDF文件")
    
    # 文件上传
    uploaded_files = st.file_uploader(
        "选择PDF文件（最多20个）",
        type=FILE_CONFIG["supported_formats"],
        accept_multiple_files=True,
        help="支持同时上传多个PDF文件",
        key="pdf_uploader"
    )
    
    if uploaded_files:
        # 检查文件数量
        if len(uploaded_files) > FILE_CONFIG["max_files"]:
            st.error(ERROR_MESSAGES["too_many_files"])
            uploaded_files = uploaded_files[:FILE_CONFIG["max_files"]]
        
        # 显示文件信息
        st.success(f"✅ 已选择 {len(uploaded_files)} 个文件")
        
        # 文件列表
        with st.expander("📋 文件详情", expanded=True):
            total_size = 0
            for i, file in enumerate(uploaded_files):
                file_size = FileManager.get_file_size_mb(file.getvalue())
                total_size += file_size
                
                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    st.text(f"{i+1}. {file.name}")
                with col2:
                    st.text(f"{file_size:.2f} MB")
                with col3:
                    if FileManager.validate_file_type(file.name, FILE_CONFIG["supported_formats"]):
                        st.text("✅")
                    else:
                        st.text("❌")
            
            st.info(f"📊 总大小: {total_size:.2f} MB")
    
    return uploaded_files

# AI解析设置
def render_ai_settings():
    """渲染AI解析设置"""
    st.header("🤖 AI解析设置")
    
    # 预设提示词选择
    prompt_type = st.selectbox(
        "选择提示词模板",
        options=list(PRESET_PROMPTS.keys()) + ["自定义"],
        help="选择预设模板或自定义输入"
    )
    
    # 根据选择显示提示词
    if prompt_type == "自定义":
        default_prompt = PRESET_PROMPTS["通用文档分析"]
    else:
        default_prompt = PRESET_PROMPTS[prompt_type]
    
    prompt = st.text_area(
        "解析提示词（Prompt）",
        value=default_prompt,
        height=200,
        help="AI将根据您的提示词来解析每一页内容"
    )
    
    # 提示词预览
    with st.expander("📝 提示词预览"):
        st.markdown(f"```\n{prompt}\n```")
    
    return prompt

# 处理PDF文件
def process_pdfs(files, prompt, api_key, max_workers, dpi, timeout):
    """处理PDF文件的主函数"""
    if not validate_api_key(api_key):
        st.error(ERROR_MESSAGES["no_api_key"])
        return
    
    # 设置处理状态
    st.session_state.processing = True
    
    # 创建处理器
    pdf_processor = PDFProcessor(dpi=dpi)
    ai_parser = AIParser(api_key=api_key, timeout=timeout)
    
    # 创建进度容器
    progress_container = st.container()
    
    with progress_container:
        # 总体进度
        total_progress = st.progress(0)
        overall_status = st.empty()
        
        # 详细信息
        detail_container = st.container()
        
        total_files = len(files)
        processed_files = []
        
        for idx, uploaded_file in enumerate(files):
            # 更新总体进度
            file_progress = idx / total_files
            total_progress.progress(file_progress)
            overall_status.text(f"处理中: {uploaded_file.name} ({idx+1}/{total_files})")
            
            with detail_container:
                st.subheader(f"📄 处理文件: {uploaded_file.name}")
                
                try:
                    # 创建输出目录结构
                    base_output_dir = Path(st.session_state.output_dir)
                    dirs = FileManager.create_directory_structure(base_output_dir, uploaded_file.name)
                    
                    # 保存原始PDF
                    st.info("💾 保存原始PDF...")
                    pdf_path = dirs['pdf'] / uploaded_file.name
                    if not FileManager.save_uploaded_file(uploaded_file, pdf_path):
                        continue
                    
                    # 拆分PDF为图片
                    st.info("✂️ 拆分PDF页面...")
                    split_progress = st.progress(0)
                    split_status = st.empty()
                    
                    # 定义PDF拆分的回调函数
                    def split_progress_callback(progress):
                        split_progress.progress(progress)
                    
                    def split_status_callback(status):
                        split_status.text(status)
                    
                    images = pdf_processor.split_pdf_to_images(
                        pdf_path, 
                        dirs['images'],
                        progress_callback=split_progress_callback,
                        status_callback=split_status_callback
                    )
                    
                    split_progress.progress(1.0)
                    split_status.text("✅ PDF拆分完成")
                    
                    if not images:
                        st.error(f"❌ {uploaded_file.name} 拆分失败")
                        continue
                    
                    st.success(f"✅ 拆分完成！共 {len(images)} 页")
                    
                    # AI解析
                    st.info("🤖 AI解析中...")
                    parse_progress = st.progress(0)
                    parse_status = st.empty()
                    
                    # 定义回调函数
                    def progress_callback(progress):
                        parse_progress.progress(progress)
                    
                    def status_callback(status):
                        parse_status.text(status)
                    
                    try:
                        # 执行AI解析
                        result = ai_parser.parse_images_batch(
                            images,
                            dirs['summaries'],
                            prompt,
                            max_workers,
                            progress_callback,
                            status_callback
                        )
                        
                        # 确保进度条显示完成
                        parse_progress.progress(1.0)
                        parse_status.text("✅ AI解析完成")
                        
                    except Exception as e:
                        parse_progress.progress(0.0)
                        parse_status.text(f"❌ AI解析失败: {str(e)}")
                        st.error(f"AI解析错误: {str(e)}")
                        
                        # 创建失败结果
                        result = {
                            'total_pages': len(images),
                            'successful': 0,
                            'failed': len(images),
                            'results': {}
                        }
                    
                    # 记录处理结果
                    file_info = {
                        'name': uploaded_file.name,
                        'pages': len(images),
                        'successful': result['successful'],
                        'failed': result['failed'],
                        'success_rate': f"{(result['successful']/result['total_pages']*100):.1f}%",
                        'output_dir': str(dirs['base']),
                        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                    
                    processed_files.append(file_info)
                    st.session_state.processed_files.append(file_info)
                    
                    # 显示处理结果
                    if result['failed'] == 0:
                        st.success(f"🎉 {uploaded_file.name} 处理完成！")
                    else:
                        st.warning(f"⚠️ {uploaded_file.name} 处理完成，但有 {result['failed']} 页失败")
                    
                except Exception as e:
                    st.error(f"❌ 处理 {uploaded_file.name} 时出错: {str(e)}")
                
                st.markdown("---")
        
        # 完成处理
        total_progress.progress(1.0)
        overall_status.text("✅ 所有文件处理完成")
    
    # 重置处理状态
    st.session_state.processing = False
    
    # 显示最终结果
    st.balloons()
    st.success(SUCCESS_MESSAGES["processing_complete"])
    
    # 结果摘要
    if processed_files:
        render_processing_summary(processed_files)

# 处理结果摘要
def render_processing_summary(processed_files):
    """渲染处理结果摘要"""
    with st.expander("📊 处理结果摘要", expanded=True):
        st.info(f"📁 结果保存位置: {st.session_state.output_dir}")
        
        # 统计信息
        total_files = len(processed_files)
        total_pages = sum(f['pages'] for f in processed_files)
        total_successful = sum(f['successful'] for f in processed_files)
        total_failed = sum(f['failed'] for f in processed_files)
        
        # 显示统计卡片
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.markdown(f"""
            <div class="metric-card">
                <h3>{total_files}</h3>
                <p>处理文件</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="metric-card">
                <h3>{total_pages}</h3>
                <p>总页数</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div class="metric-card">
                <h3>{total_successful}</h3>
                <p>成功解析</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            st.markdown(f"""
            <div class="metric-card">
                <h3>{total_failed}</h3>
                <p>解析失败</p>
            </div>
            """, unsafe_allow_html=True)
        
        # 详细表格
        if processed_files:
            df = pd.DataFrame(processed_files)
            st.dataframe(df, use_container_width=True)

# 处理历史
def render_processing_history():
    """渲染处理历史"""
    if not st.session_state.processed_files:
        return
    
    st.markdown("---")
    st.header("📊 处理历史")
    
    # 操作按钮
    col1, col2 = st.columns([4, 1])
    with col2:
        if st.button("🗑️ 清空历史"):
            st.session_state.processed_files = []
            st.rerun()
    
    # 显示历史记录
    for idx, file_info in enumerate(reversed(st.session_state.processed_files)):
        with st.expander(f"📄 {file_info['name']} - {file_info['timestamp']}"):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("页数", file_info['pages'])
                st.metric("成功", file_info['successful'])
            
            with col2:
                st.metric("失败", file_info['failed'])
                st.metric("成功率", file_info['success_rate'])
            
            with col3:
                st.text("输出目录:")
                st.code(file_info['output_dir'])
                
                # 打开文件夹按钮
                if st.button(f"📂 打开文件夹", key=f"open_{idx}"):
                    try:
                        os.system(f"open '{file_info['output_dir']}'")
                    except Exception as e:
                        st.error(f"打开文件夹失败: {str(e)}")

# 图片解析功能
def render_image_upload_and_parse():
    """渲染图片上传和解析功能"""
    st.header("🖼️ 图片智能解析")
    
    # 图片上传
    uploaded_images = st.file_uploader(
        "上传图片文件进行AI解析",
        type=['png', 'jpg', 'jpeg', 'gif', 'bmp'],
        accept_multiple_files=True,
        help="支持多种图片格式，无数量限制",
        key="image_uploader"
    )
    
    if uploaded_images:
        st.success(f"✅ 已选择 {len(uploaded_images)} 张图片")
        
        # API配置检查
        api_key = os.environ.get("ARK_API_KEY", ARK_API_CONFIG["default_api_key"])
        if not validate_api_key(api_key):
            st.error("❌ 请在侧边栏配置有效的API密钥")
            return
        
        # 提示词输入
        col1, col2 = st.columns([2, 1])
        with col1:
            prompt_type = st.selectbox(
                "选择解析模板",
                options=list(PRESET_PROMPTS.keys()) + ["自定义"],
                key="img_prompt_type"
            )
        
        with col2:
            auto_parse = st.checkbox("实时解析", help="上传后自动解析图片")
        
        # 获取提示词
        if prompt_type == "自定义":
            default_prompt = PRESET_PROMPTS["通用文档分析"]
        else:
            default_prompt = PRESET_PROMPTS[prompt_type]
        
        prompt = st.text_area(
            "解析提示词",
            value=default_prompt,
            height=120,
            key="img_prompt"
        )
        
        # 解析按钮
        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            parse_single = st.button("🔍 解析选中", key="parse_single")
        with col2:
            parse_all = st.button("🚀 批量解析", key="parse_all") 
        with col3:
            save_results = st.button("💾 保存结果", key="save_results")
        
        # 图片选择和预览
        if len(uploaded_images) > 1:
            selected_idx = st.selectbox(
                "选择要预览的图片",
                options=range(len(uploaded_images)),
                format_func=lambda x: f"{uploaded_images[x].name}",
                key="selected_image"
            )
        else:
            selected_idx = 0
        
        # 显示选中的图片
        if selected_idx < len(uploaded_images):
            selected_image = uploaded_images[selected_idx]
            
            col1, col2 = st.columns([1, 1])
            
            with col1:
                st.subheader(f"📷 {selected_image.name}")
                
                # 显示图片
                try:
                    image = Image.open(selected_image)
                    st.image(image, use_container_width=True)
                    
                    # 图片信息
                    st.info(f"尺寸: {image.size[0]}×{image.size[1]} | 格式: {image.format}")
                except Exception as e:
                    st.error(f"图片加载失败: {e}")
            
            with col2:
                st.subheader("🤖 解析结果")
                
                # 解析逻辑
                result_container = st.container()
                
                # 自动解析或手动解析
                should_parse = auto_parse or parse_single or parse_all
                
                if should_parse:
                    with result_container:
                        try:
                            # 解析单张图片
                            if parse_single or (auto_parse and len(uploaded_images) == 1):
                                result = parse_single_image_display(selected_image, prompt, api_key, selected_idx + 1)
                                if result:
                                    # 存储结果到session state
                                    if 'image_results' not in st.session_state:
                                        st.session_state.image_results = {}
                                    st.session_state.image_results[selected_image.name] = result
                            
                            # 批量解析
                            elif parse_all:
                                parse_all_images_display(uploaded_images, prompt, api_key)
                                
                        except Exception as e:
                            st.error(f"解析失败: {e}")
                
                # 显示已有结果
                if 'image_results' in st.session_state and selected_image.name in st.session_state.image_results:
                    result = st.session_state.image_results[selected_image.name]
                    st.markdown("### 📝 解析结果")
                    st.markdown(result)
                    
                    # 结果操作
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("📋 复制结果", key=f"copy_{selected_idx}"):
                            st.write("结果已准备复制")
                    with col2:
                        if st.button("🗑️ 清除结果", key=f"clear_{selected_idx}"):
                            if selected_image.name in st.session_state.image_results:
                                del st.session_state.image_results[selected_image.name]
                                st.rerun()
        
        # 批量保存功能
        if save_results and 'image_results' in st.session_state:
            save_batch_results(st.session_state.image_results)

def parse_single_image_display(uploaded_file, prompt, api_key, page_num):
    """解析单张图片并显示结果"""
    with st.spinner("🤖 AI解析中..."):
        try:
            # 创建AI解析器
            ai_parser = AIParser(api_key=api_key, timeout=60)
            
            # 转换图片为base64
            image_bytes = uploaded_file.getvalue()
            base64_image = base64.b64encode(image_bytes).decode('utf-8')
            
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
                            "text": f"这是第{page_num}张图片。{prompt}"
                        },
                    ],
                }
            ]
            
            # 调用API
            client = ai_parser.create_client()
            response = client.chat.completions.create(
                model=ai_parser.model,
                messages=messages,
                max_tokens=4096,
                temperature=0.7,
                top_p=0.9
            )
            
            result = response.choices[0].message.content
            st.success("✅ 解析完成！")
            return result
            
        except Exception as e:
            st.error(f"❌ 解析失败: {str(e)}")
            return None

def parse_all_images_display(uploaded_files, prompt, api_key):
    """批量解析图片并显示进度"""
    st.info(f"🚀 开始批量解析 {len(uploaded_files)} 张图片...")
    
    # 创建进度条
    progress_bar = st.progress(0)
    status_text = st.empty()
    results_container = st.container()
    
    try:
        ai_parser = AIParser(api_key=api_key, timeout=60)
        
        # 初始化结果存储
        if 'image_results' not in st.session_state:
            st.session_state.image_results = {}
        
        total_files = len(uploaded_files)
        
        for idx, uploaded_file in enumerate(uploaded_files):
            # 更新进度
            progress = (idx + 1) / total_files
            progress_bar.progress(progress)
            status_text.text(f"解析中: {uploaded_file.name} ({idx + 1}/{total_files})")
            
            try:
                # 解析单张图片
                result = parse_single_image_display(uploaded_file, prompt, api_key, idx + 1)
                
                if result:
                    st.session_state.image_results[uploaded_file.name] = result
                    
                    # 在结果容器中显示
                    with results_container:
                        with st.expander(f"📄 {uploaded_file.name} - 解析结果"):
                            st.markdown(result)
                
            except Exception as e:
                st.error(f"解析 {uploaded_file.name} 失败: {e}")
        
        # 完成
        progress_bar.progress(1.0)
        status_text.text("✅ 批量解析完成！")
        st.balloons()
        
    except Exception as e:
        st.error(f"批量解析失败: {e}")

def save_batch_results(results_dict):
    """保存批量解析结果"""
    if not results_dict:
        st.warning("没有可保存的结果")
        return
    
    try:
        # 创建保存目录
        save_dir = Path(st.session_state.output_dir) / "图片解析结果" / datetime.now().strftime("%Y%m%d_%H%M%S")
        save_dir.mkdir(parents=True, exist_ok=True)
        
        # 保存每个结果
        for filename, result in results_dict.items():
            # 清理文件名
            safe_filename = filename.replace('/', '_').replace('\\', '_')
            result_file = save_dir / f"{safe_filename}_解析结果.txt"
            
            with open(result_file, 'w', encoding='utf-8') as f:
                f.write(f"=== {filename} 解析结果 ===\n\n")
                f.write(result)
                f.write(f"\n\n=== 解析时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===")
        
        # 创建汇总文件
        summary_file = save_dir / "_解析汇总.txt"
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write("图片解析结果汇总\n")
            f.write("=" * 50 + "\n")
            f.write(f"解析图片数量: {len(results_dict)}\n")
            f.write(f"保存时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            for idx, (filename, result) in enumerate(results_dict.items(), 1):
                f.write(f"{idx}. {filename}\n")
                f.write("-" * 30 + "\n")
                f.write(result[:200] + "...\n\n" if len(result) > 200 else result + "\n\n")
        
        st.success(f"✅ 解析结果已保存到: {save_dir}")
        st.info(f"📁 共保存 {len(results_dict)} 个解析结果")
        
        # 清空结果
        if st.button("🗑️ 清空所有结果"):
            st.session_state.image_results = {}
            st.rerun()
            
    except Exception as e:
        st.error(f"保存失败: {e}")

# 页脚
def render_footer():
    """渲染页脚"""
    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center; color: #888; padding: 20px;'>
            <p>📄 PDF智能解析工具 v2.1</p>
            <p>Powered by Streamlit & Vision AI | 
            <a href="https://github.com" target="_blank">GitHub</a> | 
            <a href="mailto:support@example.com">技术支持</a></p>
        </div>
        """,
        unsafe_allow_html=True
    )

# 主函数
def main():
    """主函数"""
    # 渲染页面头部
    render_header()
    
    # 渲染侧边栏并获取配置
    api_key, max_workers, dpi, timeout = render_sidebar()
    
    # 主页面选项卡
    tab1, tab2 = st.tabs(["📄 PDF批量处理", "🖼️ 图片智能解析"])
    
    with tab1:
        # PDF处理功能
        st.markdown("### 📄 PDF文件批量处理")
        
        # 主页面布局
        col1, col2 = st.columns([1, 2])
        
        with col1:
            uploaded_files = render_file_upload()
        
        with col2:
            prompt = render_ai_settings()
        
        # 处理按钮
        st.markdown("---")
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            process_button = st.button(
                "🚀 开始处理", 
                type="primary", 
                disabled=not uploaded_files or st.session_state.processing,
                use_container_width=True,
                key="pdf_process_button"
            )
            
            if process_button:
                if not uploaded_files:
                    st.error(ERROR_MESSAGES["no_files"])
                elif not validate_api_key(api_key):
                    st.error(ERROR_MESSAGES["no_api_key"])
                else:
                    # 创建输出目录
                    Path(st.session_state.output_dir).mkdir(parents=True, exist_ok=True)
                    # 开始处理
                    process_pdfs(uploaded_files, prompt, api_key, max_workers, dpi, timeout)
        
        # 显示处理历史
        render_processing_history()
    
    with tab2:
        # 图片处理功能
        render_image_upload_and_parse()
    
    # 渲染页脚
    render_footer()

if __name__ == "__main__":
    main()