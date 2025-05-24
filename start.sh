#!/bin/bash

# PDF智能解析工具启动脚本

echo "🚀 启动PDF智能解析工具..."

# 虚拟环境名称
VENV_NAME="pdf_parser_env"

# 检查虚拟环境是否存在
if [ ! -d "$VENV_NAME" ]; then
    echo "❌ 虚拟环境 $VENV_NAME 不存在"
    echo "📝 请先运行 install.sh 安装依赖"
    echo "   或手动创建虚拟环境："
    echo "   python3 -m venv $VENV_NAME"
    echo "   source $VENV_NAME/bin/activate"
    echo "   pip install -r requirements.txt"
    exit 1
fi

# 激活虚拟环境
echo "🔄 激活虚拟环境 $VENV_NAME..."
source $VENV_NAME/bin/activate

# 检查激活是否成功
if [ "$VIRTUAL_ENV" = "" ]; then
    echo "❌ 虚拟环境激活失败"
    exit 1
fi

echo "✅ 虚拟环境已激活: $VIRTUAL_ENV"

# 检查是否安装了必要的依赖
echo "📦 检查依赖..."

# 检查poppler
if ! command -v pdftoppm &> /dev/null; then
    echo "❌ 未找到poppler，请先安装："
    echo "   macOS: brew install poppler"
    echo "   Ubuntu: sudo apt-get install poppler-utils"
    exit 1
fi

# 检查Python包（在虚拟环境中）
python -c "import streamlit, pdf2image, openai, pandas" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "❌ 缺少Python依赖，正在安装..."
    pip install -r requirements.txt
fi

# 设置环境变量
if [ -f .env ]; then
    export $(cat .env | xargs)
fi

echo "✅ 依赖检查完成"
echo "🌐 启动Web应用..."
echo "📱 应用将在浏览器中打开: http://localhost:8501"

# 启动Streamlit应用（在虚拟环境中）
streamlit run main_app.py --server.port 8501