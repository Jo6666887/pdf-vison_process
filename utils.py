"""
PDF智能解析工具 - 工具模块
"""

import os
import base64
import threading
import concurrent.futures
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Tuple

from PIL import Image
from openai import OpenAI
import streamlit as st

from config import ARK_API_CONFIG, ERROR_MESSAGES, SUCCESS_MESSAGES


class AIParser:
    """AI解析器"""
    
    def __init__(self, api_key: str, timeout: int = 60):
        self.api_key = api_key
        self.timeout = timeout
        self.base_url = ARK_API_CONFIG["base_url"]
        self.model = ARK_API_CONFIG["model"]
        self.lock = threading.Lock()
    
    def create_client(self) -> OpenAI:
        """创建OpenAI客户端"""
        return OpenAI(
            base_url=self.base_url,
            api_key=self.api_key,
            timeout=self.timeout
        )
    
    def image_to_base64(self, image_path: Path) -> str:
        """将图片转换为base64"""
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode('utf-8')
    
    def parse_single_image(self, image_path: Path, prompt: str, page_num: int) -> Tuple[bool, str]:
        """解析单张图片"""
        try:
            # 转换图片为base64
            base64_image = self.image_to_base64(image_path)
            
            # 创建客户端
            client = self.create_client()
            
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
                            "text": f"这是第{page_num}页的内容。{prompt}"
                        },
                    ],
                }
            ]
            
            # 调用API
            response = client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=4096,
                temperature=0.7,
                top_p=0.9
            )
            
            return True, response.choices[0].message.content
            
        except Exception as e:
            return False, str(e)
    
    def parse_images_batch(
        self, 
        image_paths: List[Path], 
        output_dir: Path, 
        prompt: str, 
        max_workers: int,
        progress_callback=None,
        status_callback=None
    ) -> Dict:
        """批量解析图片"""
        total_pages = len(image_paths)
        completed = 0
        failed = 0
        results = {}
        
        def update_progress():
            nonlocal completed, failed
            with self.lock:
                progress = completed / total_pages if total_pages > 0 else 0
                if progress_callback:
                    progress_callback(progress)
                if status_callback:
                    status_callback(f"解析进度: {completed}/{total_pages} 页 (失败: {failed})")
        
        def process_image(image_path: Path, page_num: int):
            nonlocal completed, failed
            
            success, content = self.parse_single_image(image_path, prompt, page_num)
            
            # 保存结果
            result_path = output_dir / f"{page_num}.txt"
            
            if success:
                # 保存成功结果
                with open(result_path, "w", encoding="utf-8") as f:
                    f.write(f"=== 第 {page_num} 页解析结果 ===\n\n")
                    f.write(content)
                    f.write(f"\n\n=== 解析时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===")
                
                results[page_num] = {
                    'success': True,
                    'content': content,
                    'file_path': str(result_path)
                }
            else:
                # 保存错误信息
                error_path = output_dir / f"{page_num}_error.txt"
                with open(error_path, "w", encoding="utf-8") as f:
                    f.write(f"页面 {page_num} 解析失败\n")
                    f.write(f"错误信息: {content}\n")
                    f.write(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                
                results[page_num] = {
                    'success': False,
                    'error': content,
                    'file_path': str(error_path)
                }
                failed += 1
            
            completed += 1
            update_progress()
            
            return success
        
        # 使用线程池并发处理
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = []
            for i, image_path in enumerate(image_paths):
                future = executor.submit(process_image, image_path, i+1)
                futures.append(future)
            
            # 等待所有任务完成
            concurrent.futures.wait(futures)
        
        # 创建汇总报告
        self._create_summary_report(output_dir, total_pages, completed - failed, failed, results)
        
        return {
            'total_pages': total_pages,
            'successful': completed - failed,
            'failed': failed,
            'results': results
        }
    
    def _create_summary_report(self, output_dir: Path, total: int, success: int, failed: int, results: Dict):
        """创建汇总报告"""
        summary_path = output_dir / "_summary.txt"
        
        with open(summary_path, "w", encoding="utf-8") as f:
            f.write("PDF解析汇总报告\n")
            f.write("=" * 50 + "\n")
            f.write(f"总页数: {total}\n")
            f.write(f"成功解析: {success} 页\n")
            f.write(f"解析失败: {failed} 页\n")
            f.write(f"成功率: {(success/total*100):.1f}%\n")
            f.write(f"解析时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            if failed > 0:
                f.write("失败页面详情:\n")
                f.write("-" * 30 + "\n")
                for page_num, result in results.items():
                    if not result['success']:
                        f.write(f"第 {page_num} 页: {result['error']}\n")


class FileManager:
    """文件管理器"""
    
    @staticmethod
    def create_directory_structure(base_dir: Path, filename: str) -> Dict[str, Path]:
        """创建目录结构"""
        file_dir = base_dir / filename.replace('.pdf', '')
        
        dirs = {
            'base': file_dir,
            'pdf': file_dir / 'pdf',
            'images': file_dir / 'slice-pics',
            'summaries': file_dir / 'summaries'
        }
        
        # 创建所有目录
        for dir_path in dirs.values():
            dir_path.mkdir(parents=True, exist_ok=True)
        
        return dirs
    
    @staticmethod
    def save_uploaded_file(uploaded_file, save_path: Path) -> bool:
        """保存上传的文件"""
        try:
            with open(save_path, 'wb') as f:
                f.write(uploaded_file.getvalue())
            return True
        except Exception as e:
            st.error(f"文件保存失败: {str(e)}")
            return False
    
    @staticmethod
    def get_file_size_mb(file_content: bytes) -> float:
        """获取文件大小（MB）"""
        return len(file_content) / 1024 / 1024
    
    @staticmethod
    def validate_file_type(filename: str, allowed_types: List[str]) -> bool:
        """验证文件类型"""
        return any(filename.lower().endswith(f'.{ext}') for ext in allowed_types)


class ProgressTracker:
    """进度跟踪器"""
    
    def __init__(self):
        self.progress_bars = {}
        self.status_texts = {}
    
    def create_progress_bar(self, key: str, label: str = ""):
        """创建进度条"""
        if key not in self.progress_bars:
            self.progress_bars[key] = st.progress(0)
            if label:
                self.status_texts[key] = st.empty()
    
    def update_progress(self, key: str, value: float, text: str = ""):
        """更新进度"""
        if key in self.progress_bars:
            self.progress_bars[key].progress(value)
            if text and key in self.status_texts:
                self.status_texts[key].text(text)
    
    def complete_progress(self, key: str):
        """完成进度"""
        if key in self.progress_bars:
            self.progress_bars[key].progress(1.0)
            if key in self.status_texts:
                self.status_texts[key].text("✅ 完成")


def format_file_size(size_bytes: int) -> str:
    """格式化文件大小"""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"


def validate_api_key(api_key: str) -> bool:
    """验证API密钥"""
    if not api_key or len(api_key) < 10:
        return False
    return True


def get_system_info() -> Dict:
    """获取系统信息"""
    import platform
    import psutil
    
    return {
        'platform': platform.system(),
        'python_version': platform.python_version(),
        'cpu_count': os.cpu_count(),
        'memory_gb': round(psutil.virtual_memory().total / (1024**3), 1),
        'disk_free_gb': round(psutil.disk_usage('/').free / (1024**3), 1)
    }