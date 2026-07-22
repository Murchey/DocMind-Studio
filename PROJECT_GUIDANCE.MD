# 从 0 部署项目指南

> 本文档供 AI Agent 自动执行，完成 DocMind-Studio 项目的完整部署。

---

## 前置条件

- **Python** >= 3.10
- **Node.js** >= 18（仅 VS Code 插件开发需要）
- **Git**
- **VS Code**（含 DocMind Studio 插件）
- **Pandoc**（doc-form-master 的 Markdown 转换需要）

---

## Step 1: 克隆项目

```bash
git clone <repo-url> DocMind-Studio
cd DocMind-Studio
```

---

## Step 2: 安装 Python 依赖

每个 Agent 有独立的 `requirements.txt`，按需安装。**建议创建统一虚拟环境**：

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

# ── 基础依赖（所有 Agent 通用）──
pip install python-docx lxml Pillow pyyaml

# ── doc-content-analysis ──
pip install -r ComponentAgents/doc-content-analysis/requirements.txt

# ── doc-form-master ──
pip install -r ComponentAgents/doc-form-master-main/requirements.txt

# ── excel-master ──
pip install -r ComponentAgents/excel-master-main/requirements.txt

# ── ppt-deep-summary ──
pip install -r ComponentAgents/ppt-deep-summary/requirements.txt

# ── ppt-master（需先完成 Step 3 下载）──
pip install -r ComponentAgents/ppt-master-main/requirements.txt
```

> **Pandoc 安装**（Windows）：`winget install JohnMacFarlane.Pandoc`

---

## Step 3: 下载 ppt-master 开源仓库

ppt-master 不在本仓库中，需要从 GitHub 下载并放入 `ComponentAgents/ppt-master-main/`：

```bash
# 方式 1：直接克隆
git clone https://github.com/hugohe3/ppt-master.git ComponentAgents/ppt-master-main

# 方式 2：下载 ZIP 后解压
# 访问 https://github.com/hugohe3/ppt-master/archive/refs/heads/main.zip
# 解压后将 ppt-master-main 文件夹放入 ComponentAgents/ 目录下
```

> **重要**：文件夹名称必须为 `ppt-master-main`，这是 AGENTS.md 中注册的 Agent 路径。

---

## Step 4: 验证安装

```bash
# 验证 Python 依赖
python -c "
import docx, lxml, PIL, yaml
print('基础依赖 OK')
"

# 验证各 Agent
python -c "import fitz; print('doc-content-analysis OK')"          # PyMuPDF
python -c "import pptx; print('ppt-master OK')"                     # python-pptx
python -c "import pandas, openpyxl; print('excel-master OK')"       # pandas + openpyxl
python -c "from reportlab.lib.pagesizes import A4; print('ppt-deep-summary OK')"
```

---

## Step 5: 安装 VS Code 插件（可选）

插件已随仓库提供，位于 `Extension/docmind-studio-0.2.0.vsix`。

在 VS Code 中按 `Ctrl+Shift+P` → 输入 `Extensions: Install from VSIX...` → 选择：

```
Extension/docmind-studio-0.2.0.vsix
```

或通过命令行安装：

```bash
code --install-extension Extension/docmind-studio-0.2.0.vsix
```

> 插件提供 Dashboard 进度监控、Agent/工作流/知识库浏览等功能。不安装插件不影响 Agent 本身的运行。

---

## Step 6: 配置 Python 路径（可选）

如果系统有多个 Python 版本，在 VS Code 设置中指定：

```json
{
  "docmind.pythonPath": "/path/to/your/python"
}
```

---

## 目录结构验证

部署完成后，目录结构应为：

```
DocMind-Studio/
├── AGENTS.md                          # 调度器
├── ComponentAgents/
│   ├── doc-content-analysis/          # 文档内容分析 Agent
│   ├── doc-form-master-main/          # 文档格式化 Agent
│   ├── excel-master-main/             # Excel 处理 Agent
│   ├── ppt-deep-summary/              # PPT 深度总结 Agent
│   ├── ppt-master-main/               # ⚠️ 从 GitHub 下载（hugohe3/ppt-master）
│   ├── phd-research-agent/            # 论文辅助 Agent
│   └── ppt-continuation-tool/         # PPT 续写 Agent
├── Workflows/                         # 工作流配置
├── WORKSPACE/                         # 项目工作区
├── Extension/                         # VS Code 插件
│   ├── docmind-studio-0.2.0.vsix     # 已打包插件
│   └── ...
├── PROJECT_GUIDANCE.MD                # 本文件
├── README_CN.MD                       # 中文说明
└── README.MD                          # 英文说明
```

---

## 常见问题

### Q: ppt-master 报错 `ModuleNotFoundError: No module named 'pptx'`
A: 运行 `pip install -r ComponentAgents/ppt-master-main/requirements.txt`

### Q: doc-form-master 的 PDF 导出失败
A: 需要安装 Microsoft Word 或 LibreOffice，且 `docx2pdf` 依赖 `pywin32`（Windows 自动安装）

### Q: OCR 功能不可用（处理扫描型 PDF）
A: 需要安装 Tesseract OCR + 中文语言包，或启用 PaddleOCR/EasyOCR（见 `doc-content-analysis/requirements.txt` 注释）

### Q: VS Code 插件 Dashboard 不显示进度
A: 确保通过 `docmind.startTask` 命令启动任务（stdout 实时推送），或工作流执行时 ProgressTracker 自动写入进度文件（文件监听 fallback）
