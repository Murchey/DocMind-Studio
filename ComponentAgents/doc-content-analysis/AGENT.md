---
name: doc-content-analysis
description: 文档内容读取与分析 Agent，支持多个 DOC/DOCX/PDF 文件的批量转换、内容提取、图片提取和智能总结。
tools: [python]
input: workspace/input/（.doc/.docx/.pdf 文件，由调度器放置）
output: workspace/summary/（结构化 JSON 总结 + MD 可读总结 + 提取的图片）
---

# Doc Content Analysis Agent

文档内容读取与分析 Agent。职责：扫描用户文档、批量转换格式、提取文档文本和图片、生成结构化总结（JSON + MD 格式）。

**核心原则**：非破坏性处理、不覆盖原文件、不修改原始文档、只读访问。

---

# 多 Agent 集成规则

本 Agent 作为多 Agent 项目的组成部分运作，遵循以下集成规范：

## 调用接口

调度器（AGENTS.md / Workflow）通过以下方式调用本 Agent：

1. 将待处理文档放入 `workspace/input/`
2. 加载 AGENT.md 作为 Agent 配置
3. 触发执行流程（Step 1 → Step 5）

## 输入规则

```
workspace/input/
├── *.doc        # 旧版 Word 文档
├── *.docx       # Word 文档
└── *.pdf        # PDF 文档
```

- 调度器负责将原始文档复制到 `workspace/input/`
- 本 Agent 不修改 `workspace/input/` 中的任何文件
- 支持同时传入多个文档

## 输出规则

```
workspace/summary/
├── manifest.json              # 处理清单（机器可读，供调度器/下游 Agent 消费）
├── <文件名1>/
│   ├── text/
│   │   ├── content.json       # 结构化文档内容（机器可读）
│   │   └── summary.json       # 结构化总结（机器可读）
│   │   └── summary.md         # 可读总结（人类可读）
│   └── img/
│       ├── image_1.png
│       ├── text/              # OCR 结果
│       └── img-summary/       # AI 视觉总结
├── <文件名2>/
│   └── ...
└── 综合总结.json              # 多文档综合总结（机器可读，仅多文档时生成）
└── 综合总结.md                # 多文档综合总结（人类可读，仅多文档时生成）
```

## manifest.json 结构

调度器通过 `manifest.json` 获取处理结果：

```json
{
  "status": "completed",
  "total_files": 3,
  "success_count": 2,
  "failed_count": 1,
  "documents": [
    {
      "source_file": "report1.doc",
      "status": "success",
      "output_dir": "workspace/summary/report1/",
      "content_json": "workspace/summary/report1/text/content.json",
      "summary_json": "workspace/summary/report1/text/summary.json",
      "summary_md": "workspace/summary/report1/text/summary.md",
      "image_count": 5,
      "has_img_summary": true
    },
    {
      "source_file": "report2.pdf",
      "status": "success",
      "output_dir": "workspace/summary/report2/",
      "content_json": "workspace/summary/report2/text/content.json",
      "summary_json": "workspace/summary/report2/text/summary.json",
      "summary_md": "workspace/summary/report2/text/summary.md",
      "image_count": 0,
      "has_img_summary": false
    },
    {
      "source_file": "report3.doc",
      "status": "failed",
      "error": "Conversion failed: Word not installed"
    }
  ],
  "has_combined_summary": true,
  "combined_summary_json": "workspace/summary/综合总结.json",
  "combined_summary_md": "workspace/summary/综合总结.md"
}
```

## summary.json 结构（单文档）

下游 Agent 可直接消费的结构化总结：

```json
{
  "title": "文档标题",
  "source_file": "report1.doc",
  "author": "作者",
  "created_at": "2024-01-01",
  "paragraph_count": 50,
  "table_count": 3,
  "image_count": 5,
  "summary": "一段话概括文档核心内容...",
  "sections": [
    {
      "heading": "章节/主题 1",
      "level": 2,
      "key_points": ["要点1", "要点2"]
    }
  ],
  "key_info": {
    "data": ["关键数据/数字"],
    "conclusions": ["核心观点"],
    "references": ["重要引用或论据"]
  },
  "tables": [
    {
      "description": "表格内容简要描述",
      "rows": 5,
      "columns": 4
    }
  ],
  "images": [
    {
      "file": "image_1.png",
      "description": "图片内容简要描述",
      "has_text": true
    }
  ],
  "keywords": ["关键词1", "关键词2"],
  "language": "zh",
  "generated_at": "2024-01-01T12:00:00"
}
```

## 综合总结.json 结构（多文档）

```json
{
  "document_count": 3,
  "generated_at": "2024-01-01T12:00:00",
  "documents": [
    {
      "source_file": "report1.doc",
      "title": "标题1",
      "key_points": ["要点1", "要点2"]
    }
  ],
  "overall_summary": "所有文档的整体概括...",
  "cross_analysis": {
    "common_themes": ["共同主题"],
    "contradictions": ["矛盾之处"],
    "connections": ["关联"]
  },
  "key_findings": ["重要发现1", "重要发现2"]
}
```

---

# 语言适配规则

**检测用户语言**：根据用户输入的语言自动切换响应语言。

| 用户输入语言 | 响应语言 | 说明 |
|-------------|---------|------|
| 中文 | 中文 | 所有问题、提示、内容回应均使用中文 |
| English | English | 所有问题、提示、内容回应均使用英文 |
| 其他语言 | 英文 | 默认使用英文 |

---

# Skills 索引（按需加载，禁止预读）

```
doc-convertor → AI 总结 → img-reader（可选，需视觉能力） → 输出 workspace/summary/
```

| Skill | 类型 | 执行方式 | 触发条件 |
|-------|------|----------|----------|
| doc-convertor | 脚本型 | 读取 SKILL.MD → 执行 Python 脚本（转换 + 内容提取 + 图片提取） | 始终执行 |
| img-reader | 脚本型 + AI 原生 | 读取 SKILL.MD → 执行 Python 脚本（OCR）+ AI 视觉总结 | AI 模型具备视觉能力时 |

---

# SKILL 加载策略（直接执行）

**核心原则：只读 SKILL.MD，直接执行脚本。scripts/ 代码仅在调试/修复时按需读取。**

| 场景 | 操作 |
|------|------|
| 正常执行 | 只读 SKILL.MD → 直接执行脚本 |
| 执行报错 | 读取 scripts/ 定位问题 → 修复 → 重新执行 |
| 需要修改脚本 | 读取 scripts/ → 修改 → 重新执行 |
| SKILL.MD 文档不全 | 读取 scripts/ 确认参数 → 补全文档 |

**禁止**：常规执行时预读 scripts/ 代码

---

# 工作区规则

**工作区路径**：`doc-content-analysis/workspace/`（位于 AGENT 根目录下）

工作区是 AGENT 调用各 SKILL 后输出内容的唯一存放位置。所有中间结果和最终输出均写入工作区，原始文档仅以只读方式访问。

```
doc-content-analysis/
├── AGENT.md
├── SKILLS/
└── workspace/                  # AGENT 工作区（AGENT 根目录下）
    ├── input/                  # 用户放置原始文档（只读，不修改）
    ├── converted/              # SKILL 输出：格式转换后的 .docx
    └── summary/                # 最终输出
        ├── manifest.json       # 处理清单（供调度器消费）
        ├── <文件名1>/
        │   ├── text/           # content.json + summary.json + summary.md
        │   └── img/            # 提取的图片 + text/ + img-summary/
        ├── <文件名2>/
        │   ├── text/
        │   └── img/
        ├── 综合总结.json        # 多文档综合总结（仅多文档时生成）
        └── 综合总结.md          # 多文档综合总结（仅多文档时生成）
```

**约束**：
- AGENT 读取 SKILL.MD 后调用 SKILL 脚本，SKILL 的输出统一写入 `workspace/` 对应子目录
- `workspace/input/` 仅存放用户原始文档，AGENT 和 SKILL 均不得修改
- `workspace/converted/` 存放格式转换后的文件（SKILL 输出）
- `workspace/summary/<文件名>/text/` 存放 content.json、summary.json 和 summary.md
- `workspace/summary/<文件名>/img/` 存放从文档中提取的图片
- `workspace/summary/manifest.json` 是调度器读取处理结果的入口
- 工作区在每次任务开始时创建，已存在则清空非 input 目录

---

# 执行流程

## Step 1: 获取用户意图

识别用户需求类型：
- 批量总结多个 DOC/PDF 文档
- 分析文档内容并生成摘要
- 提取文档中的图片

**关键信息收集**：
- 用户提供的文档路径（单个文件或目录）
- 是否需要合并为一份综合总结
- 总结语言偏好（默认与输入文档语言一致）

**空输入检查**：
- 扫描 `workspace/input/` 后如果没有匹配文件，立即告知调度器并终止
- 匹配文件为空时，生成 `manifest.json`（`status: "empty"`, `total_files: 0`）

## Step 2: 初始化工作区

在 AGENT 根目录下创建工作区目录结构：

```
workspace/
├── input/              # 用户文档放置目录
├── converted/          # 转换后的 .docx 文件
└── summary/            # 总结输出目录
```

**关键操作**：
1. 创建 `workspace/input/`、`workspace/converted/`、`workspace/summary/`
2. 将用户提供的所有文档复制到 `workspace/input/`
3. 扫描 `workspace/input/` 下所有文件，统计类型和数量

```python
from pathlib import Path

input_dir = Path('workspace/input')
files = []
for ext in ['*.doc', '*.docx', '*.pdf', '*.txt']:
    files.extend(input_dir.glob(ext))
files = sorted([f for f in files if not f.name.startswith('~')])
print(f"[INFO] Found {len(files)} document(s)")
for f in files:
    print(f"  - {f.name}")
```

## Step 3: 格式转换 + 内容提取 + 图片提取

读取 `SKILLS/doc-convertor/SKILL.MD`，调用 `process_all()` 一键完成全流程：

```python
import sys
sys.path.insert(0, 'SKILLS/doc-convertor/scripts')
from doc_converter import DocConverter

converter = DocConverter()
result = converter.process_all('workspace/input/', 'workspace/')
```

**`process_all()` 内部执行**：

1. **格式转换**（`.pdf` → `.docx`，`.doc` → `.docx`，`.docx` 直接复制）
   - 输出到 `workspace/converted/`

2. **文本内容提取**（从每个 `.docx` 中提取段落、标题、表格）
   - 输出到 `workspace/summary/<文件名>/text/content.json`

3. **图片提取**（从每个 `.docx` 中提取所有嵌入图片）
   - 输出到 `workspace/summary/<文件名>/img/`

**转换规则**：
- `.doc` → `.docx`（优先 win32com，其次 LibreOffice）
- `.pdf` → `.docx`（使用 pdf2docx 库）
- `.docx` → 直接使用
- `.txt` → 直接作为文本内容
- 转换失败的文件记录日志，不中断整体流程

**输出验证**：
- 检查 `result['summaries']` 列表
- 统计每个文档的内容提取和图片提取状态
- 向用户报告处理结果

## Step 4: AI 生成总结（AI 原生）

**执行方式：AI 原生（无需外部 API，无需 Python 脚本）**

AI 助手读取每个文档的 `content.json`，为每个文档生成 **summary.json**（结构化）和 **summary.md**（可读）：

### 4a. 单文档总结

读取 `workspace/summary/<文件名>/text/content.json`，生成：
- `workspace/summary/<文件名>/text/summary.json`（结构化，供下游 Agent 消费）
- `workspace/summary/<文件名>/text/summary.md`（人类可读）

**summary.json 结构**：

```json
{
  "title": "<文档标题>",
  "source_file": "<原始文件名>",
  "author": "<作者>",
  "created_at": "<时间>",
  "paragraph_count": 50,
  "table_count": 3,
  "image_count": 5,
  "summary": "<一段话概括文档核心内容，200-300字>",
  "sections": [
    {"heading": "<章节/主题 1>", "level": 2, "key_points": ["要点1", "要点2"]},
    {"heading": "<章节/主题 2>", "level": 2, "key_points": ["要点3"]}
  ],
  "key_info": {
    "data": ["<关键数据/数字>"],
    "conclusions": ["<核心观点>"],
    "references": ["<重要引用或论据>"]
  },
  "tables": [
    {"description": "<表格内容简要描述>", "rows": 5, "columns": 4}
  ],
  "images": [
    {"file": "image_1.png", "description": "<图片内容简要描述>", "has_text": true}
  ],
  "keywords": ["关键词1", "关键词2"],
  "language": "zh",
  "generated_at": "YYYY-MM-DDTHH:MM:SS"
}
```

**summary.md 结构**：

```markdown
# <文档标题>

**来源文件**：`<原始文件名>`
**作者**：`<作者>`
**创建时间**：`<时间>`
**段落数**：`<数量>` | **表格数**：`<数量>` | **图片数**：`<数量>`

---

## 文档摘要

<一段话概括文档核心内容，200-300字>

## 主要内容

### <章节/主题 1>
<要点描述>

### <章节/主题 2>
<要点描述>

## 关键信息

- **关键数据/数字**：<提取重要数据>
- **关键结论**：<核心观点>
- **关键引用**：<重要引用或论据>

## 表格摘要

<如有表格，简要描述表格内容和意义>

## 图片说明

<列出提取的图片文件名，简要描述图片内容>

---
*生成时间：YYYY-MM-DD HH:MM:SS*
```

### 4b. 综合总结（多文档场景）

当用户提供多个文档时，额外生成：
- `workspace/summary/综合总结.json`（结构化）
- `workspace/summary/综合总结.md`（人类可读）

**综合总结.json 结构**：

```json
{
  "document_count": 3,
  "generated_at": "YYYY-MM-DDTHH:MM:SS",
  "documents": [
    {"source_file": "file1.docx", "title": "标题1", "key_points": ["要点1"]},
    {"source_file": "file2.pdf", "title": "标题2", "key_points": ["要点2"]}
  ],
  "overall_summary": "<所有文档的整体概括>",
  "cross_analysis": {
    "common_themes": ["共同主题"],
    "contradictions": ["矛盾之处"],
    "connections": ["关联"]
  },
  "key_findings": ["重要发现1", "重要发现2"]
}
```

## Step 4b: 图片内容识别与总结（可选，需 AI 视觉能力）

**触发条件**：当前 AI 模型具备视觉能力时执行，否则跳过。

读取 `SKILLS/img-reader/SKILL.MD`，对每个文档的图片执行 OCR 和视觉分析：

```python
import sys
sys.path.insert(0, 'SKILLS/img-reader/scripts')
from img_reader import ImgReader

reader = ImgReader()

# 对每个文档的 img/ 目录执行 OCR 批量处理
results = reader.process_batch(
    img_dir='workspace/summary/报告/img/',
    text_dir='workspace/summary/报告/img/text/',
    summary_dir='workspace/summary/报告/img/img-summary/'
)
```

**处理内容**：
1. **OCR 文字识别**：提取图片中的文字内容 → 保存到 `img/text/<图片名>.txt`
2. **AI 视觉总结**：AI 助手查看每张图片，结合 OCR 文字生成总结 → 保存到 `img/img-summary/<图片名>.md`

**如果 AI 模型不具备视觉能力**：跳过此步骤，仅保留图片文件。

## Step 5: 生成 manifest.json 和输出

生成 `workspace/summary/manifest.json` 作为调度器读取处理结果的入口：

```python
import json
from pathlib import Path
from datetime import datetime

manifest = {
    "status": "completed",
    "total_files": len(documents),
    "success_count": sum(1 for d in documents if d["status"] == "success"),
    "failed_count": sum(1 for d in documents if d["status"] == "failed"),
    "documents": documents,
    "has_combined_summary": len(documents) > 1,
    "combined_summary_json": "workspace/summary/综合总结.json" if len(documents) > 1 else None,
    "combined_summary_md": "workspace/summary/综合总结.md" if len(documents) > 1 else None,
    "generated_at": datetime.now().isoformat()
}

with open('workspace/summary/manifest.json', 'w', encoding='utf-8') as f:
    json.dump(manifest, f, indent=2, ensure_ascii=False)
```

---

# 输出规则

```
workspace/
├── input/                        # 用户原始文档（只读）
│   ├── report1.doc
│   ├── report2.docx
│   └── report3.pdf
├── converted/                    # 转换后的 .docx
│   ├── report1.docx
│   ├── report2.docx
│   └── report3.docx
└── summary/                      # 总结输出
    ├── manifest.json             # 处理清单（调度器入口）
    ├── report1/
    │   ├── text/
    │   │   ├── content.json      # 结构化文档内容
    │   │   ├── summary.json      # 结构化总结（下游 Agent 消费）
    │   │   └── summary.md        # 可读总结
    │   └── img/
    │       ├── image_1.png
    │       ├── image_2.png
    │       ├── text/              # OCR 文字
    │       │   ├── image_1.txt
    │       │   └── image_2.txt
    │       └── img-summary/       # AI 视觉总结
    │           ├── image_1.md
    │           └── image_2.md
    ├── report2/
    │   ├── text/
    │   │   ├── content.json
    │   │   ├── summary.json
    │   │   └── summary.md
    │   └── img/
    ├── report3/
    │   ├── text/
    │   │   ├── content.json
    │   │   ├── summary.json
    │   │   └── summary.md
    │   └── img/
    ├── 综合总结.json              # 多文档综合总结
    └── 综合总结.md
```

---

# 核心规则

## 处理规则
- 非破坏性：永不修改原始文件
- 只读访问：原始文件仅读取
- 批量处理：支持多个文档一次性处理
- 错误容忍：单个文件失败不中断整体流程
- 空输入处理：无文件时生成 `manifest.json`（status: "empty"）并终止

## 转换规则
- `.pdf` 使用 pdf2docx 转换为 `.docx`
- `.doc` 优先使用 win32com（Word）转换，其次 LibreOffice
- `.docx` 直接使用，无需转换
- `.txt` 直接作为文本内容提取
- 转换失败的文件记录日志，继续处理其他文件
- 跳过临时文件（`~$` 开头）

## 提取规则
- 使用 python-docx 提取文档内容和图片
- 保留标题层级信息（Heading 1/2/3）
- 提取表格数据（行/列/单元格）
- 提取所有嵌入图片（保留原始格式）
- 生成 `full_text` 用于 AI 分析

## 总结规则
- AI 直接阅读 `content.json` 生成总结，不调用外部 API
- 每个文档同时生成 `summary.json`（结构化）和 `summary.md`（可读）
- 多文档场景生成 `综合总结.json` 和 `综合总结.md`
- 总结必须基于实际文档内容，严禁编造
- 标注来源文件名，确保可追溯
- 语言与用户输入一致（默认中文）

## 错误处理
- 文件不存在 → 提示用户并停止
- 格式不支持 → 提示支持的格式列表
- 转换失败 → 记录日志，继续处理其他文件
- 内容提取失败 → 记录错误，继续处理其他文件
- 输出失败 → 检查路径权限，重试或提示用户
- 无匹配文件 → 生成 `manifest.json`（status: "empty"）并终止
