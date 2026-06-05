---
name: docx-parser
description: DOCX 结构解析，构建统一 AST。
tools: [python]
---

# DOCX Parser

解析 DOCX 文件结构，构建统一 AST。非破坏性，仅读取。

**输入**：`.docx` 文件
**输出**：`workspace/parsed/document_ast.json`

---

# 调用方式

```bash
python SKILLS/docx-parser/scripts/parser.py
```

```python
import sys
sys.path.insert(0, 'SKILLS/docx-parser/scripts')
from parser import DocxParser

parser = DocxParser('workspace/input/input.docx')
parser.run()
# 输出: workspace/parsed/document_ast.json
```

**参数**：
- `__init__(docx_path)` - DOCX 文件路径
- `run()` - 执行解析，输出到 `workspace/parsed/document_ast.json`

---

# 解析内容

必须解析：Paragraph、Run、Style、Heading、Table、Image、Formula、Section、Relationship

---

# AST 结构

```json
{
  "metadata": {},
  "paragraphs": [{"id": 0, "type": "paragraph", "text": "", "style": "", "section": "", "runs": []}],
  "tables": [],
  "images": [],
  "formulas": [],
  "section_regions": {"cover_end": 0, "toc_start": -1, "toc_end": -1}
}
```

---

# 段落解析

提取：id、text、style、alignment、runs

## Run 类型
1. **文字 run**：`{text, bold, italic, font_name, font_size}`
2. **图片 run**：`{type: "image", image_data: "<base64>", image_format: "png"}`

---

# 区域识别

| section | 含义 | 检测规则 |
|---------|------|----------|
| cover | 封面 | 第一个 Heading 1 之前 |
| toc | 目录 | 包含「目录」「Table of Contents」 |
| body | 正文 | 其余段落 |

---

# 错误处理

DOCX 损坏/异常 → 输出日志、保留原文件、中止解析
