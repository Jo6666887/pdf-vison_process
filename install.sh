#!/bin/bash

# PDF智能解析工具安装脚本

echo "🔧 PDF智能解析工具安装程序"
echo "================================"

# 虚拟环境名称
VENV_NAME="pdf_parser_env"

# 检查操作系统
OS="$(uname -s)"
case "${OS}" in
    Linux*)     MACHINE=Linux;;
    Darwin*)    MACHINE=Mac;;
    CYGWIN*)    MACHINE=Cygwin;;
    MINGW*)     MACHINE=MinGw;;
    *)          MACHINE="UNKNOWN:${OS}"
esac

echo "🖥️  检测到操作系统: ${MACHINE}"

# 安装系统依赖
echo "📦 安装系统依赖..."

if [[ "$MACHINE" == "Mac" ]]; then
    # macOS
    if ! command -v brew &> /dev/null; then
        echo "❌ 未找到Homebrew，请先安装Homebrew"
        echo "   访问: https://brew.sh/"
        exit 1
    fi
    
    echo "🍺 使用Homebrew安装poppler..."
    brew install poppler
    
    # 检查tkinter
    echo "🖼️  检查tkinter支持..."
    if ! python3 -c "import tkinter" 2>/dev/null; then
        echo "⚠️  tkinter未安装，正在安装..."
        brew install tcl-tk python-tk@3.13
    fi
    
elif [[ "$MACHINE" == "Linux" ]]; then
    # Linux
    if command -v apt-get &> /dev/null; then
        echo "🐧 使用apt-get安装依赖..."
        sudo apt-get update
        sudo apt-get install -y poppler-utils python3-tk
    elif command -v yum &> /dev/null; then
        echo "🐧 使用yum安装依赖..."
        sudo yum install -y poppler-utils tkinter
    else
        echo "❌ 不支持的Linux发行版"
        exit 1
    fi
else
    echo "❌ 不支持的操作系统: ${MACHINE}"
    exit 1
fi

# 检查Python
echo "🐍 检查Python环境..."
if ! command -v python3 &> /dev/null; then
    echo "❌ 未找到Python3，请先安装Python3"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
echo "✅ Python版本: ${PYTHON_VERSION}"

# 创建虚拟环境
echo "🔧 创建虚拟环境..."
if [ -d "$VENV_NAME" ]; then
    echo "⚠️  虚拟环境 $VENV_NAME 已存在，删除重建..."
    rm -rf "$VENV_NAME"
fi

python3 -m venv "$VENV_NAME"
if [ $? -ne 0 ]; then
    echo "❌ 创建虚拟环境失败"
    exit 1
fi

# 激活虚拟环境
echo "🔄 激活虚拟环境..."
source "$VENV_NAME/bin/activate"

if [ "$VIRTUAL_ENV" = "" ]; then
    echo "❌ 虚拟环境激活失败"
    exit 1
fi

echo "✅ 虚拟环境已激活: $VIRTUAL_ENV"

# 升级pip（在虚拟环境中）
echo "⬆️  升级pip..."
pip install --upgrade pip

# 安装Python依赖（在虚拟环境中）
echo "📚 安装Python依赖包..."
pip install -r requirements.txt

# 验证安装
echo "🔍 验证安装..."
python -c "
try:
    import streamlit
    import pdf2image
    import openai
    import pandas
    import psutil
    print('✅ 所有依赖包安装成功')
except ImportError as e:
    print(f'❌ 依赖包导入失败: {e}')
    exit(1)
"

if [ $? -eq 0 ]; then
    echo ""
    echo "🎉 安装完成！"
    echo ""
    echo "📋 使用说明："
    echo "   1. 运行: ./start.sh"
    echo "   2. 在浏览器中打开: http://localhost:8501"
    echo "   3. 配置API密钥并开始使用"
    echo ""
    echo "💡 提示："
    echo "   - 虚拟环境已创建在: $VENV_NAME/"
    echo "   - 如需手动激活: source $VENV_NAME/bin/activate"
    echo ""
    echo "📖 更多信息请查看 README.md"
else
    echo "❌ 安装验证失败，请检查错误信息"
    exit 1
fi