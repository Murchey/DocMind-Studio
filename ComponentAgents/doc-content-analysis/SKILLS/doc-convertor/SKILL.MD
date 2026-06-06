---
name: doc-convertor
description: DOC/DOCX/PDF 文档转换、内容提取与图片提取，支持单文件和批量处理。
tools: [python]
---

# Doc Convertor

DOC/DOCX/PDF 文档转换与内容提取。将 .doc/.pdf 转换为 .docx，提取文档全文内容和图片，用于后续总结。

**输入**：`.doc` / `.docx` / `.pdf` 文件（放置到 `workspace/input/`）
**输出**：转换后的 `.docx` → 内容提取到 `workspace/summary/<文件名>/text/`，图片提取到 `workspace/summary/<文件名>/img/`

---

# 工作流概览

```
workspace/input/
├── report.docx    ──→  提取文本 + 图片
├── paper.pdf      ──→  PDF→DOCX 转换 ──→  提取文本 + 图片
└── thesis.doc     ──→  .doc→.docx 转换 ──→  提取文本 + 图片
        ↓
workspace/summary/
├── report/
│   ├── text/        # content.json（结构化内容）
│   └── img/         # 提取的图片
├── paper/
│   ├── text/
│   └── img/
└── thesis/
    ├── text/
    └── img/
```

---

# 调用方式

## 全流程处理（推荐）

一键完成：格式转换 → 内容提取 → 图片提取，按文档名分目录输出。

```python
import sys
sys.path.insert(0, 'SKILLS/doc-convertor/scripts')
from doc_converter import DocConverter

converter = DocConverter()
result = converter.process_all('workspace/input/', 'workspace/')
# result: {
#   'convert_results': [...],
#   'summaries': [
#     {'file_name': 'report', 'docx_path': '...', 'text_dir': '...', 'img_dir': '...', 'content_success': True, 'image_count': 3},
#     ...
#   ],
#   'converted_dir': '.../workspace/converted',
#   'summary_dir': '.../workspace/summary'
# }
```

```bash
python SKILLS/doc-convertor/scripts/doc_converter.py process_all workspace/input/ workspace/
```

## 单文件转换

```python
converter = DocConverter()

# .doc → .docx
result = converter.convert('workspace/input/report.doc')

# .pdf → .docx
result = converter.convert('workspace/input/paper.pdf')
```

```bash
python SKILLS/doc-convertor/scripts/doc_converter.py convert <input_path> [output_path]
```

## 批量转换

```python
converter = DocConverter()
results = converter.batch_convert('workspace/input/', 'workspace/converted/')
# 自动处理 .doc → .docx、.pdf → .docx、.docx 直接复制
```

```bash
python SKILLS/doc-convertor/scripts/doc_converter.py batch_convert <input_dir> [output_dir]
```

## 内容提取

```python
converter = DocConverter()
content = converter.extract_content('workspace/converted/report.docx')
# content: {'title': '...', 'paragraphs': [...], 'tables': [...], 'full_text': '...'}
```

```bash
python SKILLS/doc-convertor/scripts/doc_converter.py extract <docx_path>
```

## 图片提取

```python
converter = DocConverter()
result = converter.extract_images('workspace/converted/report.docx', 'workspace/summary/report/img/')
# result: {'success': True, 'image_count': 5, 'images': ['image_1.png', ...]}
```

```bash
python SKILLS/doc-convertor/scripts/doc_converter.py extract_images <docx_path> <output_dir>
```

---

# 方法参考

| 方法 | 说明 |
|------|------|
| `convert(input_path, output_path=None)` | 统一转换入口：自动识别 .doc/.pdf/.docx |
| `convert_doc(input_path, output_path=None)` | .doc → .docx |
| `convert_pdf(input_path, output_path=None)` | .pdf → .docx |
| `batch_convert(input_dir, output_dir=None)` | 批量转换目录下所有文档 |
| `extract_content(docx_path)` | 提取 .docx 文本和表格内容 |
| `extract_images(docx_path, output_dir)` | 提取 .docx 中的图片 |
| `extract_batch(input_dir)` | 批量提取目录下所有 .docx 内容 |
| `process_all(input_dir, workspace_dir)` | **全流程**：转换 → 提取内容 → 提取图片 |

---

# 转换方法

## .doc → .docx

按优先级尝试：

| 优先级 | 方法 | 适用环境 | 依赖 |
|--------|------|----------|------|
| 1 | win32com | Windows + 已安装 Word | `pywin32` |
| 2 | LibreOffice | 跨平台 | LibreOffice 已安装 |

## .pdf → .docx

| 方法 | 依赖 | 说明 |
|------|------|------|
| pdf2docx | `pdf2docx` | Python 库，保留格式和布局 |

---

# 内容提取能力

`extract_content()` 返回结构化内容：

```json
{
  "file_name": "report.docx",
  "file_path": "workspace/converted/report.docx",
  "title": "文档标题",
  "author": "作者",
  "created_at": "2024-01-01",
  "paragraph_count": 120,
  "table_count": 5,
  "paragraphs": [
    {"text": "段落内容", "style": "Heading 1", "is_heading": true, "level": 1},
    {"text": "正文内容...", "style": "Normal", "is_heading": false, "level": 0}
  ],
  "tables": [
    {"rows": [["A", "B"], ["1", "2"]]}
  ],
  "full_text": "完整的纯文本内容..."
}
```

---

# 图片提取能力

`extract_images()` 返回：

```json
{
  "success": true,
  "source": "workspace/converted/report.docx",
  "output_dir": "workspace/summary/report/img",
  "image_count": 5,
  "images": [
    "workspace/summary/report/img/image_1.png",
    "workspace/summary/report/img/image_2.jpg"
  ]
}
```

---

# AGENT 集成

在 AGENT.md 中作为 Step 3 调用：

```
Step 3: 文档转换与内容提取
- 读取 SKILLS/doc-convertor/SKILL.md
- 调用 process_all() 一键完成：
  1. .pdf → .docx 转换
  2. .doc → .docx 转换
  3. 提取每个 .docx 的文本内容 → workspace/summary/<文件名>/text/content.json
  4. 提取每个 .docx 的图片 → workspace/summary/<文件名>/img/
```

---

# 错误处理

- Word/LibreOffice 未安装 → 输出错误信息、提示用户安装
- pdf2docx 未安装 → 输出错误信息、提示 `pip install pdf2docx`
- 文件损坏 → 输出错误日志、保留原文件、继续处理下一个文件
- 批量处理中某个文件失败 → 记录错误、不中断整体流程
- 文件不存在 → 返回错误结果、继续处理
