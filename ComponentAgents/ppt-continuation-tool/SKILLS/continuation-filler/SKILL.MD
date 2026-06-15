---
name: continuation-filler
description: 执行续写计划，生成新幻灯片并合并到原 PPT
tools: [python]
---

# Continuation Filler

执行续写计划，生成新幻灯片并合并到原 PPT。

## 功能说明

本 SKILL 负责 PPT 续写流程的执行阶段，包括：
1. 检查续写计划中的文本容量
2. 执行续写计划，生成新幻灯片
3. 将新幻灯片合并到原 PPT
4. 输出完整的 PPTX 文件

## 输入/输出

**输入**：
- `{workspace}/input/*.pptx`：外部半完成 PPT
- `{workspace}/analysis/completion_plan.json`：续写计划
- `{workspace}/analysis/slide_library.json`：幻灯片库分析结果

**输出**：
- `{workspace}/output/*.pptx`：继续完成的 PPTX

## 脚本说明

### template_fill_pptx.py
PPTX 模板填充工具，支持分析、脚手架、检查和应用。

```bash
# 分析幻灯片库
python3 SKILLS/continuation-filler/scripts/template_fill_pptx.py analyze <deck.pptx> -o slide_library.json

# 生成脚手架计划
python3 SKILLS/continuation-filler/scripts/template_fill_pptx.py scaffold slide_library.json -o fill_plan.json

# 检查计划容量
python3 SKILLS/continuation-filler/scripts/template_fill_pptx.py check-plan slide_library.json fill_plan.json

# 应用计划
python3 SKILLS/continuation-filler/scripts/template_fill_pptx.py apply <deck.pptx> fill_plan.json -o output.pptx
```

## 执行流程

### Step 1: 检查文本容量
```python
import sys
sys.path.insert(0, 'SKILLS/continuation-filler/scripts')
from template_fill_pptx import main as template_fill_main

# 检查续写计划的文本容量
check_report = check_capacity(
    slide_library='{workspace}/analysis/slide_library.json',
    fill_plan='{workspace}/analysis/completion_plan.json',
    output_path='{workspace}/analysis/check_report.json'
)
```

### Step 2: 执行续写计划
```python
import sys
sys.path.insert(0, 'SKILLS/continuation-filler/scripts')
from template_fill_pptx import main as template_fill_main

# 应用续写计划
result = execute_fill(
    source_pptx='{workspace}/input/*.pptx',
    fill_plan='{workspace}/analysis/completion_plan.json',
    output_path='{workspace}/output/'
)
```

### Step 3: 输出 manifest.json
```python
import json
from pathlib import Path

manifest = {
    "status": "completed",
    "total_slides": 15,
    "original_slides": 8,
    "new_slides": 7,
    "source_files": ["input.pptx", "资料.docx"],
    "output_file": "{workspace}/output/项目名_completed_20260609_120000.pptx",
    "preview_url": "http://localhost:5050",
    "generated_at": "2026-06-09T12:00:00"
}

with open('{workspace}/output/manifest.json', 'w', encoding='utf-8') as f:
    json.dump(manifest, f, indent=2, ensure_ascii=False)
```

### Step 4: 启动预览服务器（可选）
```python
import sys
sys.path.insert(0, 'SKILLS/pptx-preview/scripts')
from pptx_preview_server import start_preview_server

# 启动预览服务器
server_url = start_preview_server(
    pptx_path='{workspace}/output/*.pptx',
    port=5050,
    auto_open=True
)
print(f"预览服务器已启动: {server_url}")
```

## 输出格式

### check_report.json
```json
{
  "total_warnings": 2,
  "warnings": [
    {
      "slide_number": 4,
      "slot_id": "body",
      "warning_type": "body_too_long",
      "message": "文本长度超过目标槽位容量",
      "suggestion": "压缩内容或选择更大的布局"
    }
  ]
}
```

### manifest.json
```json
{
  "status": "completed",
  "total_slides": 15,
  "original_slides": 8,
  "new_slides": 7,
  "source_files": ["input.pptx", "资料.docx"],
  "output_file": "{workspace}/output/项目名_completed_20260609_120000.pptx",
  "preview_url": "http://localhost:5050",
  "generated_at": "2026-06-09T12:00:00"
}
```
