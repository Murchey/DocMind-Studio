| name | ppt_analyst |
| ---- | ----------- |
| description | 读取 PPTParser 输出的结构化数据，进行内容分析与大纲构建。支持 Human-in-the-loop 审阅。 |

# PPTAnalyst Skill

## 核心目标

对 PPTParser 提取的结构化数据进行语义分析、核心观点提炼和大纲构建。

## 触发时机

- PPTParser 解析完成后
- 用户要求"分析 PPT"、"提取核心观点"、"生成大纲"

## 调用方式

```bash
python SKILLS/PPTAnalyst/scripts/ppt_analyst.py <parsed.json> [outline.json]
```

```python
from ppt_analyst import analyze, to_json
result = analyze(parsed_data, output_path="outline.json")
```

## 输出 JSON 结构

```json
{
  "presentation_overview": {
    "title": "string",
    "total_slides": 0,
    "main_topic": "string",
    "key_themes": ["string"]
  },
  "outline": {
    "sections": [
      {
        "section_id": 1,
        "title": "string",
        "key_points": [
          {
            "point": "string",
            "supporting_data": "string",
            "source_slide": 1,
            "confidence": "high|medium|low"
          }
        ],
        "sub_sections": []
      }
    ]
  },
  "insights": {
    "strengths": ["string"],
    "gaps": ["string"],
    "recommendations": ["string"]
  },
  "metadata": {
    "analysis_timestamp": "string",
    "requires_user_review": true
  }
}
```

## Agent 约束

- 每个关键要点必须标注 `source_slide`
- 不确定的推断设 `confidence: low`
- 严禁编造内容
- 输出 `requires_user_review: true` 触发用户审阅

## 注意事项

- 依赖 PPTParser 输出，不能直接处理 .pptx
- 复杂图表仅分析标题和类型
