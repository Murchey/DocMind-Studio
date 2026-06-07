| name | ppt_batch_process |
| ---- | ----------------- |
| description | 批量处理多个PPT文件，为每个文件生成独立的解析和分析结果 |

# PPTBatchProcess Skill

## 核心目标

一次处理多个PPT文件，为每个文件生成独立的解析和分析结果。

## 触发时机

- 用户有多个PPT文件需要批量处理
- 用户要求"批量处理"、"批量总结"、"批量分析"

## 调用方式

```bash
python SKILLS/PPTBatchProcess/scripts/ppt_batch_process.py <输入目录> [-o <输出目录>]
```

```bash
# 处理目录下所有PPT
python SKILLS/PPTBatchProcess/scripts/ppt_batch_process.py /path/to/pptx/dir -o /path/to/output

# 处理多个指定文件（逗号分隔）
python SKILLS/PPTBatchProcess/scripts/ppt_batch_process.py file1.pptx,file2.pptx,file3.pptx -o /path/to/output
```

## 输入参数

| 参数 | 说明 |
|------|------|
| `input` | PPT文件路径、目录路径或多个文件路径（用逗号分隔） |
| `-o, --output` | 输出目录（可选，默认为输入路径下的 batch_output） |

## 输出结构

```
output_dir/
├── manifest.json               # 处理清单（供调度器消费）
├── <文件名1>/
│   ├── parsed.json             # PPTParser 解析结果
│   ├── parsed.md               # PPTParser Markdown输出
│   └── outline.json            # PPTAnalyst 分析结果
├── <文件名2>/
│   ├── parsed.json
│   ├── parsed.md
│   └── outline.json
└── ...
```

## manifest.json 结构

与 AGENT.md 中定义的 manifest.json 结构一致：

```json
{
  "status": "completed",
  "total_files": 4,
  "success_count": 4,
  "failed_count": 0,
  "documents": [
    {
      "source_file": "example.pptx",
      "status": "success",
      "output_dir": "output/example",
      "parsed_json": "output/example/parsed.json",
      "parsed_md": "output/example/parsed.md",
      "outline_json": "output/example/outline.json",
      "slide_count": 10,
      "main_topic": "主要主题",
      "key_themes": ["主题1", "主题2"],
      "warnings": []
    }
  ],
  "generated_at": "2024-01-01T00:00:00"
}
```

## 依赖

- PPTParser Skill
- PPTAnalyst Skill

## 注意事项

- 仅处理 `.pptx` 文件
- 每个文件独立处理，互不影响
- 失败的文件不会中断整个批量流程
- 临时文件（`~$` 开头）自动跳过
