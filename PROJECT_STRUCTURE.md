# 📁 项目结构说明

## 文件组织

```
pdf-parser-app/
├── main_app.py          # 🎯 主应用文件（推荐使用）
├── config.py            # ⚙️ 配置文件
├── utils.py             # 🔧 工具模块
├── requirements.txt     # 📦 Python依赖列表
├── README.md           # 📖 项目说明文档
├── PROJECT_STRUCTURE.md # 📁 本文件
├── .env.example        # 🔑 环境变量模板
├── install.sh          # 🔧 自动安装脚本
├── start.sh            # 🚀 启动脚本
├── run.sh              # 🚀 备用启动脚本
├── app.py              # 📄 基础版本（参考）
└── app_improved.py     # 📄 改进版本（参考）
```

## 文件说明

### 核心文件

- **`main_app.py`** - 主应用程序，集成了所有功能的完整版本
- **`config.py`** - 配置管理，包含所有设置项和预设提示词
- **`utils.py`** - 工具模块，包含PDF处理、AI解析等核心功能

### 配置文件

- **`requirements.txt`** - Python依赖包列表
- **`.env.example`** - 环境变量配置模板

### 脚本文件

- **`install.sh`** - 自动安装脚本，一键安装所有依赖
- **`start.sh`** - 主启动脚本（推荐使用）
- **`run.sh`** - 备用启动脚本

### 文档文件

- **`README.md`** - 完整的项目说明和使用指南
- **`PROJECT_STRUCTURE.md`** - 本文件，项目结构说明

### 参考文件

- **`app.py`** - 基础版本的应用，包含核心功能
- **`app_improved.py`** - 改进版本，添加了更多功能

## 使用建议

### 🎯 推荐使用流程

1. **首次使用**:
   ```bash
   ./install.sh    # 自动安装依赖
   ./start.sh      # 启动应用
   ```

2. **日常使用**:
   ```bash
   ./start.sh      # 直接启动
   ```

### 📝 自定义配置

如果需要修改默认配置，可以编辑以下文件：

- **`config.py`** - 修改默认设置、添加新的预设提示词
- **`.env`** - 设置环境变量（从.env.example复制）

### 🔧 开发扩展

如果需要添加新功能：

1. **添加新的工具函数** → 编辑 `utils.py`
2. **添加新的配置项** → 编辑 `config.py`
3. **修改界面布局** → 编辑 `main_app.py`

## 模块依赖关系

```
main_app.py
├── config.py (配置管理)
├── utils.py (核心功能)
│   ├── PDFProcessor (PDF处理)
│   ├── AIParser (AI解析)
│   ├── FileManager (文件管理)
│   └── ProgressTracker (进度跟踪)
└── requirements.txt (外部依赖)
```

## 输出目录结构

应用运行后会在指定目录创建以下结构：

```
输出目录/
└── PDF文件名/
    ├── pdf/              # 原始PDF文件
    ├── slice-pics/       # 拆分的图片
    └── summaries/        # AI解析结果
        ├── 1.txt
        ├── 2.txt
        ├── ...
        └── _summary.txt  # 汇总报告
```

## 版本说明

- **main_app.py** - v2.0 完整功能版本 ⭐ **推荐**
- **app_improved.py** - v1.5 改进版本
- **app.py** - v1.0 基础版本

建议使用 `main_app.py`，它包含了最完整的功能和最好的用户体验。