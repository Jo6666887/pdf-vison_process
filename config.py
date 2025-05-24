"""
PDF智能解析工具配置文件
"""

import os
from pathlib import Path

# API配置
ARK_API_CONFIG = {
    "base_url": "https://ark.cn-beijing.volces.com/api/v3",
    "model": "ep-20250425135316-55rdv",
    "default_api_key": ""
}

# 文件处理配置
FILE_CONFIG = {
    "max_files": 20,
    "supported_formats": ['pdf'],
    "default_dpi": 200,
    "max_dpi": 400,
    "min_dpi": 100
}

# 并发配置
CONCURRENCY_CONFIG = {
    "max_workers": 5,
    "default_workers": 2,
    "default_timeout": 60,
    "max_timeout": 300
}

# 输出配置
OUTPUT_CONFIG = {
    "default_output_dir": str(Path.home() / "Desktop" / "PDF解析结果"),
    "pdf_subdir": "pdf",
    "images_subdir": "slice-pics",
    "summaries_subdir": "summaries"
}

# UI配置
UI_CONFIG = {
    "page_title": "PDF智能解析工具",
    "page_icon": "📄",
    "layout": "wide",
    "sidebar_state": "expanded"
}

# 预设提示词
PRESET_PROMPTS = {
    
    "设计方案分析": """设计项目名称是【！！！用户需要主动输入，避免有的页面没有项目名字！】
你是一款视觉识别和文档理解模型。当前输入的图片均来自**景观建筑设计项目**文档。请对每张单页图片进行文字提取和语义解析，并**仅**返回一行 UTF-8 编码的 JSON 字符串，键和值均为中文，键顺序保持不变，不要输出任何其他文本或换行。格式如下：

{
  "Page_type": "<页面类型，仅填“封面页”、“目录”、“章节页”或“内容页”>",
  "page_name": "<该页主标题；若无明确标题，请基于景观设计主题自行概括一句>",
  "tag": [ "<与页面高关联的景观/建筑关键词1>", "<关键词2>", "...（3-8 项）" ],
  "page_content": "<用不超过 200 字概述该页全部信息，突出景观设计要点>",
  "project_name": "<项目或文档整体名称；若用户未提供且页内无明确项目名，则留空>"
}

规则：
1. 仅输出一行 JSON 字符串，无换行、注释或额外字符。  
2. `tag` 必须是中括号包裹的字符串数组，元素用英文逗号分隔。  
3. 如某字段无法确定，用空字符串 "" 占位，但键名仍要保留。  
4. 不要对中文做 Unicode 转义；保持可读中文。  
5. 值中不得包含除单双引号外的转义符。  
6. 键名及顺序不得增删、更改。
""",
    
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

请以Markdown表格格式输出。""",
    
    "财务报表分析": """请分析这张财务报表图片：
1. 识别报表类型（资产负债表/利润表/现金流量表等）
2. 提取主要财务数据
3. 计算关键财务指标
4. 标注异常或重要项目

请以结构化格式输出分析结果。""",
    
    "证件识别": """请识别这张证件图片中的信息：
1. 证件类型
2. 姓名/名称
3. 证件号码
4. 有效期
5. 发证机关
6. 其他关键信息

请以JSON格式输出识别结果。"""
}

# 错误消息
ERROR_MESSAGES = {
    "no_api_key": "❌ 请先配置API Key！",
    "no_files": "❌ 请先上传PDF文件！",
    "too_many_files": "⚠️ 最多只能同时上传20个文件！",
    "pdf_split_failed": "❌ PDF拆分失败",
    "api_call_failed": "❌ API调用失败",
    "file_save_failed": "❌ 文件保存失败"
}

# 成功消息
SUCCESS_MESSAGES = {
    "pdf_split_success": "✅ PDF拆分完成！",
    "processing_complete": "🎉 所有文件处理完成！",
    "file_uploaded": "✅ 文件上传成功"
}

def get_env_var(key, default=None):
    """获取环境变量"""
    return os.environ.get(key, default)

def create_output_structure(base_dir, filename):
    """创建输出目录结构"""
    base_path = Path(base_dir)
    file_dir = base_path / filename.replace('.pdf', '')
    
    dirs = {
        'base': file_dir,
        'pdf': file_dir / OUTPUT_CONFIG['pdf_subdir'],
        'images': file_dir / OUTPUT_CONFIG['images_subdir'],
        'summaries': file_dir / OUTPUT_CONFIG['summaries_subdir']
    }
    
    # 创建所有目录
    for dir_path in dirs.values():
        dir_path.mkdir(parents=True, exist_ok=True)
    
    return dirs
