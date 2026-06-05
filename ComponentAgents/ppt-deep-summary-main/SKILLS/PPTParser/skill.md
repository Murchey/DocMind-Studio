| name | ppt_parser |
| ---- | ---------- |
| description | 深度解析 .pptx 文件，提取结构化内容（标题、文本、表格、图片、超链接、备注、图表），输出 JSON/Markdown。 |

# PPTParser Skill

## 核心目标

对 PPTX 文件进行底层解包和结构化提取，为下游 PPTAnalyst 提供干净的输入数据。

## 触发时机

- 用户上传 `.pptx` 文件要求分析
- 用户询问 PPT 内容或结构
- 调用 PPTAnalyst 之前必须执行

## 调用方式

```bash
python SKILLS/PPTParser/scripts/ppt_parser.py <pptx路径> [输出JSON] [输出Markdown]
```

```python
from ppt_parser import parse, to_json, to_markdown
result = parse("demo.pptx", json_output="output.json", md_output="output.md")
```

## 输出 JSON 结构

```json
{
  "presentation_title": "string",
  "slide_count": 0,
  "slides": [
    {
      "slide_number": 1,
      "title": "string",
      "layout_name": "string",
      "texts": [{"level": 0, "text": "string"}],
      "notes": ["string"],
      "tables": [{"rows": [[]], "row_count": 0, "col_count": 0}],
      "images": [{"filename": "string", "content_type": "string", "width": 0, "height": 0}],
      "hyperlinks": [{"text": "string", "url": "string"}],
      "charts": [{"chart_type": "string", "title": "string"}],
      "raw_markdown": "string"
    }
  ],
  "warnings": []
}
```

## Agent 约束

- 严禁总结或改写提取内容
- warnings 不为空时告知用户
- notes/tables/hyperlinks 需纳入分析

## 注意事项

- 仅支持 `.pptx` 文件
- 图片/图表仅提取引用信息
- 错误记录在 warnings 中，不中断流程
