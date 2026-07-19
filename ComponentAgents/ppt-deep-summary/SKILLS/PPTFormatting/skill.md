| name | ppt_formatting |
| ---- | -------------- |
| description | 读取 PPTAnalyst 输出的分析大纲，进行排版渲染与强制溯源，生成格式美观的最终报告。 |

# PPTFormatting Skill

## 核心目标

将 PPTAnalyst 的分析大纲转换为格式美观、溯源清晰的最终报告。

## 触发时机

- PPTAnalyst 完成分析后
- 用户要求"生成报告"、"排版输出"

## 调用方式

```bash
python SKILLS/PPTFormatting/scripts/ppt_formatting.py <outline.json> [report.md] [--format markdown|html]
```

```python
from ppt_formatting import format_report, to_markdown, to_html
result = format_report(analysis_data, output_path="report.md", format_type="markdown")
```

## 输出结构

Markdown/HTML 报告包含：
- 概览（标题、页数、主题）
- 分析大纲（章节 → 要点 + 溯源标签）
- 洞察分析（亮点、缺口、建议）
- 生成时间戳

## Agent 约束

- 每个结论标注 `(Source: Slide X)`
- 低置信度要点标注 `[待确认]`
- 严禁修改原始分析内容

## 注意事项

- 依赖 PPTAnalyst 输出
- 默认 Markdown 格式，`--format html` 切换
