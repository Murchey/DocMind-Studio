---
name: footnote-processor
description: 脚注和尾注格式处理器，支持学术论文脚注/尾注标准化
tools: [python]
---

# Footnote Processor

脚注和尾注格式处理器，用于学术论文脚注/尾注的标准化处理。

## 功能

- **脚注检测**：自动检测文档中的脚注（footnote）和尾注（endnote）
- **脚注格式化**：按照学术论文标准格式化脚注文本
- **编号标准化**：支持带圈数字（①, ②, ③...）、阿拉伯数字（1, 2, 3...）等编号格式
- **每页重新编号**：支持脚注编号每页自动重新开始
- **分隔线设置**：脚注与正文之间的分隔线样式
- **字体字号**：中文宋体（小五号）、英文 Times New Roman（比中文小半号）
- **行距控制**：单倍行距
- **顶格书写**：无首行缩进

## 使用方法

```python
import sys
sys.path.insert(0, 'SKILLS/footnote-processor/scripts')
from footnote_processor import FootnoteProcessor

processor = FootnoteProcessor('workspace/output/formatted.docx')
processor.run()
processor.save('workspace/output/formatted.docx')
```

## 参数

| 参数 | 类型 | 说明 |
|------|------|------|
| docx_path | str | DOCX 文件路径 |
| config_path | str | 配置文件路径（可选，默认使用内置配置） |

## 配置项

脚注配置位于模板文件的 `footnote` 部分：

```yaml
footnote:
  enabled: true
  font_size_cn: 10.5      # 中文字号（磅），通常为小五号（10.5pt）
  font_size_en: 9          # 英文字号（磅），通常比中文小半号
  line_spacing: single     # 脚注行距：single/1.5/double
  numbering: circled       # 编号格式：circled（带圈数字）/arabic（阿拉伯数字）/roman（罗马数字）
  restart_per_page: true   # 每页重新编号
  separator_length: 25     # 分隔线长度（毫米）
  font_name_cn: 宋体       # 中文字体
  font_name_en: Times New Roman  # 英文字体
  first_line_indent: 0     # 首行缩进（磅），0表示顶格书写
```

## 处理内容

### 脚注格式
- 中文字体：宋体（小五号，10.5pt）
- 英文字体：Times New Roman（9pt，比中文小半号）
- 行距：单倍行距
- 编号：带圈数字（①, ②, ③...）或阿拉伯数字（1, 2, 3...）
- 编号位置：每页重新编号
- 段落缩进：顶格书写，无首行缩进

### 尾注格式
- 位置：文档末尾或节末
- 字体字号：与脚注相同
- 编号：阿拉伯数字

### 分隔线
- 位置：页面底部，脚注上方
- 样式：细实线（0.5pt）
- 长度：页面宽度的 1/3

## 编号格式说明

| 格式 | 说明 | 示例 |
|------|------|------|
| circled | 带圈数字 | ①, ②, ③...⑳ |
| arabic | 阿拉伯数字 | 1, 2, 3... |
| roman | 罗马数字 | i, ii, iii... |

## 输出

处理后的 DOCX 文件，脚注/尾注格式符合学术论文规范。

## 依赖

- python-docx
- lxml

## 注意事项

- 脚注内容中的公式和图片会被保护
- 编号格式会自动与文档中现有格式保持一致
- 处理不会改变脚注的语义内容
- 带圈数字最多支持 20 个（①-⑳），超出后自动切换为阿拉伯数字
