---
name: img-reader
description: 图片内容读取与总结，支持 OCR 文字识别和 AI 视觉分析。
tools: [python]
---

# Image Reader

图片内容读取与总结。对文档中提取的图片进行 OCR 文字识别，并利用 AI 视觉能力生成图片内容总结。

**输入**：`workspace/summary/<文件名>/img/` 目录下的图片文件
**输出**：OCR 文字 → `text/` 子目录，图片总结 → `img-summary/` 子目录

---

# 工作流概览

```
workspace/summary/<文件名>/img/
├── image_1.png              # 原始图片
├── image_2.jpg
├── text/                    # OCR 识别结果
│   ├── image_1.txt          # 图片中的文字内容
│   └── image_2.txt
└── img-summary/             # AI 视觉总结
    ├── image_1.md           # 图片内容 + 文字总结
    └── image_2.md
```

**触发条件**：仅当 AI 模型具备视觉能力时执行此 SKILL。

---

# 调用方式

## 批量处理（推荐）

对指定目录下所有图片执行 OCR 提取：

```python
import sys
sys.path.insert(0, 'SKILLS/img-reader/scripts')
from img_reader import ImgReader

reader = ImgReader()
results = reader.process_batch(
    img_dir='workspace/summary/报告/img/',
    text_dir='workspace/summary/报告/img/text/',
    summary_dir='workspace/summary/报告/img/img-summary/'
)
```

```bash
python SKILLS/img-reader/scripts/img_reader.py process_batch <img_dir> <text_dir> <summary_dir>
```

## 单张图片 OCR

```python
reader = ImgReader()
result = reader.extract_text('workspace/summary/报告/img/image_1.png')
# result: {'success': True, 'text': '识别出的文字', 'has_text': True}
```

```bash
python SKILLS/img-reader/scripts/img_reader.py extract_text <image_path>
```

---

# 方法参考

| 方法 | 说明 |
|------|------|
| `extract_text(image_path)` | 对单张图片执行 OCR，返回识别文字 |
| `process_batch(img_dir, text_dir, summary_dir)` | 批量处理目录下所有图片 |

---

# OCR 能力

`extract_text()` 返回：

```json
{
  "success": true,
  "image_path": "workspace/summary/报告/img/image_1.png",
  "has_text": true,
  "text": "图片中识别出的文字内容...",
  "text_length": 150
}
```

**OCR 引擎优先级**：

| 优先级 | 引擎 | 依赖 | 说明 |
|--------|------|------|------|
| 1 | PaddleOCR | `paddleocr`, `paddlepaddle` | 中文识别效果最佳 |
| 2 | EasyOCR | `easyocr` | 支持多语言，无需额外安装 |
| 3 | Tesseract | `pytesseract`, Tesseract OCR | 需系统安装 Tesseract |

---

# AI 视觉总结（AI 原生）

**执行方式：AI 原生（无需 Python 脚本）**

OCR 完成后，AI 助手直接查看图片，结合 OCR 文字生成总结：

### 总结文件结构（`img-summary/<图片名>.md`）

```markdown
# 图片分析：<图片文件名>

**来源文档**：`<原始文档名>`
**图片路径**：`<图片路径>`

---

## 图片描述

<AI 对图片视觉内容的描述，包括图表类型、关键数据、视觉元素等>

## 文字内容

<OCR 识别出的文字内容，如无文字则标注"图片中未检测到文字">

## 内容总结

<结合图片视觉内容和文字内容的综合总结，提炼关键信息>

---
*生成时间：YYYY-MM-DD HH:MM:SS*
```

---

# AGENT 集成

在 AGENT.md 的 Step 4（AI 生成总结）之后、Step 5（生成输出）之前插入：

```
Step 4b: 图片内容识别与总结（可选，需 AI 视觉能力）
- 判断当前 AI 模型是否具备视觉能力
- 如果具备：
  1. 读取 SKILLS/img-reader/SKILL.MD
  2. 对每个文档的 img/ 目录调用 process_batch() 执行 OCR
  3. AI 查看每张图片，结合 OCR 文字生成 img-summary/*.md
- 如果不具备：跳过此步骤，仅保留图片文件
```

---

# 错误处理

- OCR 引擎未安装 → 跳过 OCR，记录警告，继续处理
- 图片格式不支持 → 记录错误，继续处理下一张
- 图片中无文字 → `has_text: false`，生成空 txt 文件
- 批量处理中某张图片失败 → 记录错误，不中断整体流程
