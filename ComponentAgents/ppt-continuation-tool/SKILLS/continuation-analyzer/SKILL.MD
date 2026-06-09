---
name: continuation-analyzer
description: 分析外部 PPT 结构，识别已完成/未完成页面，转换 DOCX 参考资料为 Markdown
tools: [python]
---

# Continuation Analyzer

分析外部 PPT 结构，识别已完成/未完成页面，转换 DOCX 参考资料为 Markdown。

## 功能说明

本 SKILL 负责 PPT 续写流程的分析阶段，包括：
1. 将 DOCX 参考资料转换为 Markdown 格式
2. 分析外部 PPT 的幻灯片结构
3. 识别已完成和未完成的页面
4. 生成续写计划

## 输入/输出

**输入**：
- `{workspace}/input/*.pptx`：外部半完成 PPT
- `{workspace}/input/*.docx`：参考资料

**输出**：
- `{workspace}/sources/*.md`：转换后的 Markdown 文件
- `{workspace}/analysis/slide_library.json`：幻灯片库分析结果
- `{workspace}/analysis/completion_plan.json`：续写计划

## 脚本说明

### ppt_to_md.py
将 PPTX 转换为 Markdown 格式，提取文本、表格、演讲者备注和图片。

```bash
python3 SKILLS/continuation-analyzer/scripts/ppt_to_md.py <input.pptx> -o <output.md>
```

### doc_to_md.py
将 DOCX 转换为 Markdown 格式，支持多种文档格式。

```bash
python3 SKILLS/continuation-analyzer/scripts/doc_to_md.py <input.docx> -o <output.md>
```

## 执行流程

### Step 1: 转换 DOCX 参考资料
```python
import sys
sys.path.insert(0, 'SKILLS/continuation-analyzer/scripts')
from doc_to_md import convert_doc_to_md

# 转换所有 DOCX 文件
convert_doc_to_md('{workspace}/input/', '{workspace}/sources/')
```

### Step 2: 分析 PPT 结构
```python
import sys
sys.path.insert(0, 'SKILLS/continuation-analyzer/scripts')
from ppt_analyzer import analyze_ppt

result = analyze_ppt(
    pptx_path='{workspace}/input/*.pptx',
    output_path='{workspace}/analysis/slide_library.json'
)
```

### Step 3: 生成续写计划
```python
import json
from pathlib import Path

# 读取幻灯片库
with open('{workspace}/analysis/slide_library.json', 'r', encoding='utf-8') as f:
    slide_library = json.load(f)

# 读取参考资料
sources = []
for md_file in Path('{workspace}/sources/').glob('*.md'):
    with open(md_file, 'r', encoding='utf-8') as f:
        sources.append(f.read())

# 生成续写计划
completion_plan = generate_completion_plan(slide_library, sources)

# 保存续写计划
with open('{workspace}/analysis/completion_plan.json', 'w', encoding='utf-8') as f:
    json.dump(completion_plan, f, indent=2, ensure_ascii=False)
```

## 输出格式

### slide_library.json
```json
{
  "source_pptx": "input.pptx",
  "total_slides": 10,
  "slides": [
    {
      "slide_number": 1,
      "page_type": "cover",
      "text_summary": "封面页面",
      "slots": [
        {
          "slot_id": "s01_sh4",
          "role": "title",
          "geometry": {"left": 100000, "top": 100000, "width": 8000000, "height": 1000000},
          "old_text": "原标题"
        }
      ],
      "tables": [],
      "charts": []
    }
  ]
}
```

### completion_plan.json
```json
{
  "schema": "ppt_continuation_plan.v1",
  "source_pptx": "input.pptx",
  "existing_slides": [1, 2, 3],
  "new_slides": [
    {
      "target_slide": 4,
      "purpose": "content",
      "content_source": "sources/资料.md#章节1",
      "layout_template": "content",
      "replacements": [
        {
          "slot_id": "title",
          "text": "新标题"
        },
        {
          "slot_id": "body",
          "text": "新内容"
        }
      ],
      "notes": "演讲者备注"
    }
  ]
}
```
