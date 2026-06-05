---
name: markdown-converter
description: Markdown 无缝转换为 DOCX。
tools: [python, pandoc]
---

# Markdown Converter

将 Markdown 文件转换为 DOCX 格式，支持数学公式、表格、代码块等。

**输入**：`.md` / `.txt` 文件（含 Markdown 内容）
**输出**：`.docx` 文件

---

# 调用方式

## 命令行

```bash
python SKILLS/markdown-converter/scripts/md_converter.py <input_file> [output_file]
```

## Python API

```python
import sys
sys.path.insert(0, 'SKILLS/markdown-converter/scripts')
from md_converter import MarkdownConverter

converter = MarkdownConverter()
result = converter.convert('input.md', 'output.docx')
# result: {'success': True, 'output_path': 'output.docx'}
```

**参数**：
- `convert(input_path, output_path=None, template_config=None)` - 转换 Markdown 为 DOCX
  - `input_path` - 输入 Markdown 文件路径
  - `output_path` - 输出 DOCX 文件路径（可选）
  - `template_config` - 模板配置（可选，用于格式化）
- 返回：转换结果字典

---

# 功能特性

| 特性 | 说明 |
|------|------|
| **数学公式** | 自动检测 LaTeX 公式，转换为 OMML/MathML |
| **表格** | 支持 Markdown 表格 |
| **代码块** | 支持围栏代码块（```） |
| **标题** | 自动转换为 Word 标题样式 |
| **列表** | 支持有序/无序列表 |
| **图片** | 支持嵌入图片 |
| **链接** | 支持超链接 |

---

# 数学公式处理

## 自动格式化

检测未格式化的 LaTeX 公式并添加 `$` 分隔符：

```python
# 输入（未格式化）
"f(x) = x^2 + 2x + 1"

# 输出（已格式化）
"$f(x) = x^2 + 2x + 1$"
```

## 公式模式

| 模式 | 语法 | 示例 |
|------|------|------|
| 行内公式 | `$...$` | `$x^2$` |
| 块级公式 | `$$...$$` | `$$\int_0^1 x dx$$` |

---

# 依赖要求

## 必需依赖

- **pandoc** - 文档转换引擎
  - 安装：`winget install JohnMacFarlane.Pandoc`
  - 或：`choco install pandoc`

## Python 依赖

- 无额外依赖（使用标准库）

---

# 输出格式

```json
{
  "success": true,
  "input_path": "input.md",
  "output_path": "output.docx",
  "file_size": 12345,
  "has_math": true,
  "pages_estimated": 5
}
```

---

# AGENT 集成

在 AGENT.md 中添加为可选输入格式：

```
Step 2c: Markdown 转换（如输入为 .md/.txt）
- 检测输入文件是否为 Markdown 格式
- 如果是，调用 markdown-converter 转换为 .docx
- 转换后继续正常的格式化流程
```

---

# 错误处理

- pandoc 未安装 → 输出错误信息、提示安装命令
- 公式格式错误 → 尝试自动修复、输出警告
- 转换失败 → 中止流程、保留原文件
