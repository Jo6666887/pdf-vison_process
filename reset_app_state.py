#!/usr/bin/env python3
"""
应用状态重置脚本 - 用于重置卡住的Streamlit应用状态
"""

import streamlit as st
import time
import os
import signal

def reset_streamlit_state():
    """重置Streamlit应用状态"""
    print("🔄 重置Streamlit应用状态...")
    
    # 1. 停止现有的Streamlit进程
    print("🛑 停止现有Streamlit进程...")
    os.system("pkill -f streamlit")
    time.sleep(2)
    
    # 2. 清理临时文件
    print("🧹 清理临时文件...")
    temp_dirs = [
        ".streamlit",
        "__pycache__",
        "*.pyc"
    ]
    
    for pattern in temp_dirs:
        os.system(f"rm -rf {pattern}")
    
    # 3. 重启应用
    print("🚀 重新启动应用...")
    print("💡 请在新终端中运行: ./start.sh")
    print("🌐 应用地址: http://localhost:8501")

def check_and_fix_processing_state():
    """检查并修复可能卡住的处理状态"""
    print("🔍 检查应用处理状态...")
    
    # 检查是否有PDF解析结果但Streamlit卡住
    import os
    from pathlib import Path
    
    desktop_results = Path.home() / "Desktop" / "PDF解析结果"
    if desktop_results.exists():
        pdf_folders = [d for d in desktop_results.iterdir() if d.is_dir()]
        
        for pdf_folder in pdf_folders:
            slice_pics = pdf_folder / "slice-pics"
            summaries = pdf_folder / "summaries"
            
            if slice_pics.exists() and len(list(slice_pics.glob("*.png"))) > 0:
                print(f"✅ 发现已完成的PDF拆分: {pdf_folder.name}")
                
                if summaries.exists() and len(list(summaries.glob("*.txt"))) > 0:
                    print(f"✅ 发现已完成的AI解析: {pdf_folder.name}")
                else:
                    print(f"⚠️  PDF拆分完成但AI解析未完成: {pdf_folder.name}")
                    print("   可以在Streamlit中重新运行AI解析")

def main():
    """主函数"""
    print("🛠️  Streamlit应用状态修复工具")
    print("=" * 40)
    
    # 检查当前状态
    check_and_fix_processing_state()
    
    print("\n" + "=" * 40)
    print("🔧 修复选项:")
    print("1. 重置Streamlit应用状态")
    print("2. 仅检查处理状态")
    print("3. 退出")
    
    choice = input("\n请选择操作 (1-3): ").strip()
    
    if choice == "1":
        reset_streamlit_state()
    elif choice == "2":
        print("✅ 状态检查完成")
    elif choice == "3":
        print("👋 退出")
    else:
        print("❌ 无效选择")

if __name__ == "__main__":
    main() 