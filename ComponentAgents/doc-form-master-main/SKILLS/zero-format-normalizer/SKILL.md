---
name: zero-format-normalizer
description: 零格式文档格式化。
tools: [python]
---

# Zero Format Normalizer

从零格式 DOCX 提取文本，按模板生成规范文档。

**输入**：源 DOCX + `template_config` + `edited_config`（可选）
**输出**：`workspace/output/formatted.docx`

---

# 调用方式

```bash
python SKILLS/zero-format-normalizer/scripts/zero_format_normalizer.py <input.docx> <output.docx> [template.json] [edited_config.json]
```

```python
import sys
sys.path.insert(0, 'SKILLS/zero-format-normalizer/scripts')
from zero_format_normalizer import ZeroFormatNormalizer

normalizer = ZeroFormatNormalizer(
    'workspace/input/input.docx',
    'workspace/validated/template_config.json',
    'workspace/validated/edited_config.json'  # 可选：用户预览确认后的配置
)
normalizer.run('workspace/output/formatted.docx')
# 输出: workspace/output/formatted.docx
```

**参数**：
- `__init__(source_docx_path, template_config_path=None, edited_config_path=None)` - 源 DOCX 路径、模板配置路径、用户编辑配置路径
- `run(output_path)` - 生成格式化 DOCX

---

# 处理流程

1. 提取文本内容（忽略原始格式）
2. 检测文档结构（封面/目录/标题/正文/参考文献）
3. 应用模板配置生成新文档（封面 → 正文 → 参考文献）
4. **最后插入 TOC 域代码**（封面之后、正文/摘要之前）
5. 创建分节、设置页眉页脚
6. **参考文献自动分页**（添加分页符+分节符，确保参考文献在新页开始）

---

# TOC 插入规则

目录在文本处理**最后一步**插入：
- 插入位置：封面页之后一节
- 如果有摘要（「摘要」「Abstract」），插入到摘要页之前
- 如果无摘要，插入到第一个 Heading 之前

---

# 结构检测

- **封面**：第一个标题之前的段落
- **目录**：包含「目录」「Table of Contents」
- **参考文献**：包含「参考文献」「References」

---

# 标题检测

| 级别 | 模式 | 示例 |
|------|------|------|
| H1 | `第X章/节/部分` | 第一章 |
| H2 | 中文数字（一、二、三） | 一、xxx |
| H2 | 关键词+冒号 | 引言：xxx |
| H3 | 数字编号（1. xxx） | 1. xxx |

**上下文感知**：短段落（≤40字）前后都是长段落（>100字）→ H2

---

# 封面配置

```json
{
  "cover": {
    "enabled": true,
    "school_name": "XX大学",
    "school_font": "宋体",
    "school_size": 18,
    "title": {"text": "课程作业", "font": "黑体", "size": 22},
    "logo": {"enabled": false, "image_data": "", "image_path": ""}
  }
}
```

Logo 支持：base64 编码、文件路径

---

# 标题格式

- 使用 Word 内置样式（Heading 1/2/3）
- 使用模板配置的字体
- 颜色强制黑色（RGB 0,0,0）

---

# 分节规则

文档结构：封面 → 分节 → 摘要（如有） → 分节 → 目录 → 分节 → 正文 → 分节 → 参考文献（如有）

| 节 | 内容 | 页眉 | 页脚 |
|----|------|------|------|
| 1 | 封面 | 无 | 无 |
| 2 | 目录 | 无 | 无 |
| 3 | 正文 | 有 | 有（页码从1开始） |
| 4 | 参考文献 | 有 | 有（续正文页码） |

---

# 错误处理

源文件不存在/损坏 → 抛出异常、保留原文件
