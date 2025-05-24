#!/usr/bin/env python3
"""
环境测试脚本 - 验证虚拟环境和依赖
"""

import sys
import os
from pathlib import Path

def test_environment():
    """测试当前环境配置"""
    print("🔍 环境配置测试")
    print("=" * 40)
    
    # 检查虚拟环境
    virtual_env = os.environ.get('VIRTUAL_ENV')
    if virtual_env:
        print(f"✅ 虚拟环境: {virtual_env}")
    else:
        print("❌ 未检测到虚拟环境")
    
    # 检查Python路径
    print(f"🐍 Python路径: {sys.executable}")
    print(f"🐍 Python版本: {sys.version}")
    
    # 检查依赖包
    print("\n📦 依赖包测试:")
    dependencies = [
        'streamlit',
        'pdf2image', 
        'openai',
        'pandas',
        'PIL',
        'psutil'
    ]
    
    all_ok = True
    for dep in dependencies:
        try:
            __import__(dep)
            print(f"   ✅ {dep}")
        except ImportError:
            print(f"   ❌ {dep}")
            all_ok = False
    
    # 检查系统命令
    print("\n🖥️ 系统工具测试:")
    system_tools = ['pdftoppm', 'pdftocairo']
    
    for tool in system_tools:
        if os.system(f"which {tool} > /dev/null 2>&1") == 0:
            print(f"   ✅ {tool}")
        else:
            print(f"   ❌ {tool}")
    
    # 检查项目文件
    print("\n📁 项目文件检查:")
    required_files = [
        'main_app.py',
        'config.py', 
        'utils.py',
        'requirements.txt',
        'start.sh',
        'install.sh'
    ]
    
    for file_name in required_files:
        file_path = Path(file_name)
        if file_path.exists():
            print(f"   ✅ {file_name}")
        else:
            print(f"   ❌ {file_name}")
            all_ok = False
    
    print("\n" + "=" * 40)
    if all_ok:
        print("🎉 环境检查通过！可以正常使用")
    else:
        print("⚠️ 部分检查失败，请检查上述错误")
    
    return all_ok

if __name__ == "__main__":
    test_environment() 