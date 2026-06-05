---
name: table-processor
description: 表格格式化处理（对齐、边框、单元格格式、题注、图片保护）
tools: [python-docx, lxml]
---

# table-processor

## 功能描述

对 DOCX 文档中的表格进行学术论文标准格式化处理。

### 核心能力
1. **表格对齐** - 表格整体居中对齐
2. **表格边框** - 三线表样式（顶线、底线粗实线，栏目线细实线，无竖线）
3. **单元格格式** - 字体（宋体五号）、段落对齐（居中/左对齐）、行距（单倍行距）
4. **表头行格式** - 首行黑体加粗，居中对齐
5. **表格题注** - 检测并格式化「表 X-X」题注，黑体五号居中，位于表格上方
6. **题注与表格关联** - 题注段落与表格保持同页（keep with next）
7. **图片保护** - 保留表格单元格内的图片，不压缩不删除
8. **单元格边距** - 设置适当的内边距

### 使用方式

独立调用：
```python
from table_processor import TableProcessor

processor = TableProcessor('output.docx', 'template_config.json')
processor.run()
processor.save('output.docx')
```

作为后处理步骤（在 format-normalizer 或 zero-format-normalizer 之后）：
```python
from table_processor import TableProcessor

processor = TableProcessor('workspace/output/formatted.docx', 'workspace/validated/template_config.json')
processor.run()
processor.save('workspace/output/formatted.docx')
```

### 参数说明

| 参数 | 类型 | 说明 |
|------|------|------|
| docx_path | str | DOCX 文件路径 |
| config_path | str | 模板配置文件路径（JSON） |

### 输出

- 直接修改传入的 DOCX 文件中的表格和题注格式
- 返回处理报告（表格数量、题注数量、修改统计）

### 表格格式规范

依据 GB/T 7713.1-2006 学术论文格式标准：

| 项目 | 规范 |
|------|------|
| 表格位置 | 居中 |
| 边框 | 三线表（顶线/底线 1.5pt，栏目线 0.75pt） |
| 表头字体 | 黑体 10.5pt（五号），居中 |
| 表体字体 | 宋体 10.5pt（五号），居中或左对齐 |
| 行距 | 单倍行距 |
| 题注位置 | 表格上方 |
| 题注字体 | 黑体 10.5pt（五号） |
| 题注对齐 | 居中 |
| 题注格式 | 「表 X-X  题注内容」 |
| 题注与表格 | 保持同页 |

### 表格题注检测规则

| 模式 | 示例 |
|------|------|
| `表\s*\d+[-.]\d+` | 表 1-1 xxx、表2.1 xxx |
| `表\s*\d+` | 表1 xxx、表 2 xxx |
| `Table\s*\d+` | Table 1 xxx |
| `表格\s*\d+` | 表格1 xxx |

### 注意事项

- 不修改表格内容（文本/数据）
- 保留表格单元格内的图片和公式
- 三线表样式仅修改边框，不增删行列
- 如已有题注格式则保留原内容，仅调整格式
- 兼容 WPS 和 LibreOffice
