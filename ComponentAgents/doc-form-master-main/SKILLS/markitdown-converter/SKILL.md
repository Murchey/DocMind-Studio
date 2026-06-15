---
name: markitdown-converter
description: 统一文档格式转换器，支持 DOCX ↔ MD、PDF/PPTX/XLSX/HTML → MD → DOCX。
tools: [python, pandoc]
---

# Document Converter

统一文档格式转换器，集成 markitdown 和 pandoc，支持双向转换。

**输入**：多种文档格式（.md, .docx, .pdf, .pptx, .xlsx, .html 等）
**输出**：Markdown 或 DOCX 文件

---

# 转换逻辑

| 输入格式 | 输出格式 | 使用引擎 | 说明 |
|---------|---------|---------|------|
| `.md` / `.txt` | `.docx` | pandoc | 支持数学公式（LaTeX → MathML） |
| `.docx` | `.md` | markitdown | 保留标题、列表、表格结构 |
| `.pdf` | `.md` | markitdown | 文本提取、OCR（可选） |
| `.pptx` | `.md` | markitdown | 幻灯片内容、备注 |
| `.xlsx` | `.md` | markitdown | 表格数据 |
| `.html` | `.md` | markitdown | 网页内容 |
| 任意格式 | `.docx` | markitdown + pandoc | 两步转换：先转 MD，再转 DOCX |

---

# 调用方式

## 命令行

```bash
# MD → DOCX
python SKILLS/markitdown-converter/scripts/markitdown_converter.py input.md output.docx

# DOCX → MD
python SKILLS/markitdown-converter/scripts/markitdown_converter.py document.docx output.md

# PDF → MD
python SKILLS/markitdown-converter/scripts/markitdown_converter.py report.pdf output.md

# PDF → DOCX（两步转换）
python SKILLS/markitdown-converter/scripts/markitdown_converter.py report.pdf output.docx
```

## Python API

```python
import sys
sys.path.insert(0, 'SKILLS/markitdown-converter/scripts')
from markitdown_converter import MarkItDownConverter

converter = MarkItDownConverter()

# MD → DOCX
result = converter.convert('input.md', 'output.docx')

# DOCX → MD
result = converter.convert('document.docx', 'output.md')

# 任意格式 → DOCX
result = converter.convert_to_docx('report.pdf', 'output.docx')
```

---

# API 方法

| 方法 | 说明 | 参数 |
|------|------|------|
| `convert(input, output)` | 智能转换（自动判断方向） | 输入路径、输出路径（可选） |
| `convert_to_docx(input, output)` | 任意格式 → DOCX | 输入路径、输出路径（可选） |
| `extract_text(input)` | 提取纯文本 | 输入路径 |
| `get_metadata(input)` | 获取元数据 | 输入路径 |
| `batch_convert(in_dir, out_dir)` | 批量转换 | 输入目录、输出目录 |

---

# 功能特性

## Markdown → DOCX

| 特性 | 说明 |
|------|------|
| **数学公式** | 自动检测 LaTeX 公式，转换为 MathML |
| **表格** | 支持 Markdown 表格 |
| **代码块** | 支持围栏代码块 |
| **标题** | 自动转换为 Word 标题样式 |
| **列表** | 支持有序/无序列表 |

## DOCX/其他格式 → Markdown

| 特性 | 说明 |
|------|------|
| **多格式支持** | DOCX、PDF、PPTX、XLSX、HTML 等 |
| **结构保留** | 保留标题、列表、表格、链接 |
| **元数据提取** | 自动提取标题、字数、表格数等 |

---

# 依赖要求

## 必需依赖

- **markitdown** - 多格式 → Markdown 转换
  - 安装：`pip install 'markitdown[all]'`

## 可选依赖

- **pandoc** - Markdown → DOCX 转换
  - 安装：`winget install JohnMacFarlane.Pandoc`
  - 仅在需要 MD → DOCX 转换时使用

---

# 输出格式

```json
{
  "success": true,
  "input_path": "document.docx",
  "output_path": "document.md",
  "content": "# 标题\n\n正文内容...",
  "metadata": {
    "title": "文档标题",
    "word_count": 1500,
    "table_count": 3
  }
}
```

---

# AGENT 集成

在 AGENT.md 中作为统一转换步骤：

```
Step 2: 文档格式转换
- 检测输入文件格式
- 如果是 .md/.txt → 调用 markitdown-converter 转换为 .docx
- 如果是 .docx → 跳过（直接进入解析）
- 如果是其他格式 → 调用 markitdown-converter 转换为 .md，再转为 .docx
```

---

# 错误处理

- 格式不支持 → 输出错误信息、提示支持格式
- pandoc 未安装 → 提示安装命令
- 文件损坏 → 输出错误日志、保留原文件
- 转换失败 → 中止流程、输出详细错误信息