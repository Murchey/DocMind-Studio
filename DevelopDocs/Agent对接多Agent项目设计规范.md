# Agent 对接多 Agent 项目设计规范

> 本文档定义了 DocMind Studio 中各 Agent 作为多 Agent 系统组成部分运作时的对接规范。
> 以 `doc-content-analysis` 为参考实现，提炼通用设计原则。

---

## 1. 架构总览

```
┌─────────────────────────────────────────────────────────┐
│                    AGENTS.md（调度器）                     │
│         调用 WORKFLOW → 根据用户需求调度 AGENT             │
└──────────┬──────────────────────────┬────────────────────┘
           │                          │
           ▼                          ▼
┌─────────────────────┐    ┌─────────────────────┐
│  doc-content-analysis│    │  其他 Agent          │
│  （文档总结 Agent）    │    │  （格式转换/知识库等） │
└──────────┬──────────┘    └──────────┬──────────┘
           │                          │
           ▼                          ▼
┌─────────────────────┐    ┌─────────────────────┐
│  SKILLS/             │    │  SKILLS/             │
│  ├── doc-convertor   │    │  ├── ...             │
│  └── img-reader      │    │  └── ...             │
└─────────────────────┘    └─────────────────────┘
```

### 层级关系

| 层级 | 文件 | 职责 |
|------|------|------|
| 调度层 | `AGENTS.md` + `Workflows/*.md` | 解析用户需求，选择 Agent，编排执行顺序 |
| Agent 层 | `ComponentAgents/<agent>/AGENT.md` | 定义工作流、输入输出契约、调用 SKILL |
| Skill 层 | `ComponentAgents/<agent>/SKILLS/<skill>/SKILL.MD` | 提供具体能力（脚本型/AI 原生型） |

---

## 2. AGENT.md 规范

每个 Agent 的 `AGENT.md` 必须包含以下部分：

### 2.1 Front Matter（必须）

```yaml
---
name: <agent-name>                    # Agent 唯一标识
description: <一句话描述>               # 调度器用于匹配用户需求
tools: [python]                       # 依赖的工具
input: <输入路径和格式说明>              # 调度器写入数据的位置
output: <输出路径和格式说明>             # 调度器/下游 Agent 读取结果的位置
---
```

### 2.2 多 Agent 集成契约（必须）

```markdown
# 多 Agent 集成契约

## 调用接口
- 调度器如何触发本 Agent

## 输入契约
- 输入文件的路径、格式、命名规范

## 输出契约
- 输出文件的路径、格式、命名规范
- manifest.json 结构（处理清单）
- 核心输出 JSON 结构（供下游消费）
```

### 2.3 工作区规则（必须）

```markdown
# 工作区规则

**工作区路径**：`<agent-name>/workspace/`（位于 AGENT 根目录下）

**约束**：
- 工作区是 SKILL 输出的唯一存放位置
- input/ 只读
- 每次任务开始时清空非 input 目录
```

### 2.4 执行流程（必须）

每个 Step 必须包含：
- **目的**：这一步做什么
- **调用的 SKILL**：读取哪个 SKILL.MD
- **代码示例**：如何调用 SKILL 脚本
- **输出位置**：结果写入哪里

### 2.5 核心规则（必须）

```markdown
# 核心规则

## 处理规则
## 输出规则
## 错误处理
```

---

## 3. 输出契约规范

### 3.1 manifest.json（必须）

每个 Agent 执行完成后必须在输出目录生成 `manifest.json`，作为调度器读取结果的入口：

```json
{
  "status": "completed | failed | empty",
  "total_files": 3,
  "success_count": 2,
  "failed_count": 1,
  "documents": [
    {
      "source_file": "原始文件名",
      "status": "success | failed",
      "output_dir": "输出目录路径",
      "error": "失败原因（仅 status=failed 时）"
    }
  ],
  "generated_at": "ISO 8601 时间戳"
}
```

**字段说明**：

| 字段 | 类型 | 必须 | 说明 |
|------|------|------|------|
| `status` | string | 是 | 整体处理状态：`completed` / `failed` / `empty` |
| `total_files` | int | 是 | 输入文件总数 |
| `success_count` | int | 是 | 成功处理数 |
| `failed_count` | int | 是 | 失败处理数 |
| `documents` | array | 是 | 每个文件的处理结果 |
| `documents[].source_file` | string | 是 | 原始文件名 |
| `documents[].status` | string | 是 | 单文件处理状态 |
| `documents[].output_dir` | string | 否 | 输出目录（成功时） |
| `documents[].error` | string | 否 | 错误信息（失败时） |
| `generated_at` | string | 是 | ISO 8601 时间戳 |

### 3.2 结构化输出 JSON（必须）

每个 Agent 的核心输出必须同时提供：
- **JSON 格式**：供下游 Agent 程序化消费
- **MD 格式**：供人类阅读

JSON 结构由各 Agent 自行定义，但必须遵循：
- 包含 `source_file` 字段（可追溯）
- 包含 `generated_at` 字段（时间戳）
- 包含 `document_type` 字段（文档类型：`knowledge` | `requirement`）
- 使用 UTF-8 编码
- 使用 `indent=2` 格式化

### 3.2.1 需求文档输出规范

当文档被识别为需求类文档时，summary.json 必须包含：

```json
{
  "document_type": "requirement",
  "requirement_type": "schedule | excel | general",
  "target_agent": "schedule-agent | excel-master",
  "requirements": {
    "task_description": "任务描述",
    "constraints": ["约束条件1", "约束条件2"],
    "inputs": ["所需输入1", "所需输入2"],
    "expected_output": "期望输出描述"
  }
}
```

**需求类型映射**：

| requirement_type | 目标 Agent | 场景 |
|-----------------|------------|------|
| `schedule` | schedule-agent | 排课、会议安排、日程规划 |
| `excel` | excel-master | 表格分析、数据对比、图表生成 |
| `general` | 根据内容判断 | 其他需求 |

### 3.3 输出目录结构规范

```
<agent>/workspace/
├── input/                  # 输入（只读，调度器放置）
├── <中间产物目录>/          # SKILL 产出的中间文件
└── summary/                # 最终输出
    ├── manifest.json       # 处理清单（调度器入口）
    ├── <项目1>/
    │   └── <输出文件>       # 结构化 JSON + 可读 MD
    ├── <项目2>/
    │   └── <输出文件>
    └── 综合总结.json        # 跨项目综合（可选）
```

---

## 4. SKILL.MD 规范

### 4.1 Front Matter（必须）

```yaml
---
name: <skill-name>
description: <一句话描述>
tools: [python]
---
```

### 4.2 内容结构（必须）

```markdown
# <Skill 名称>

## 功能说明
## 输入/输出
## 调用方式（Python 代码示例）
## 方法参考（API 表格）
## 错误处理
```

### 4.3 SKILL 类型

| 类型 | 说明 | 示例 |
|------|------|------|
| 脚本型 | 提供 Python 脚本，Agent 直接执行 | doc-convertor |
| AI 原生型 | Agent 自身能力（如视觉、语言理解），无需脚本 | AI 总结、图片描述 |
| 混合型 | 脚本 + AI 原生结合 | img-reader（OCR 脚本 + AI 视觉总结） |

### 4.4 SKILL 加载策略

**核心原则：只读 SKILL.MD，直接执行脚本。scripts/ 代码仅在调试/修复时按需读取。**

| 场景 | 操作 |
|------|------|
| 正常执行 | 只读 SKILL.MD → 直接执行脚本 |
| 执行报错 | 读取 scripts/ 定位问题 → 修复 → 重新执行 |
| 需要修改脚本 | 读取 scripts/ → 修改 → 重新执行 |
| SKILL.MD 文档不全 | 读取 scripts/ 确认参数 → 补全文档 |

---

## 5. 工作区规范

### 5.1 路径规范

- 工作区位于 Agent 根目录下：`ComponentAgents/<agent>/workspace/`
- 使用相对路径引用工作区内部文件
- 工作区不在 `.gitignore` 中排除（供调试使用）

### 5.2 目录权限

| 目录 | 权限 | 说明 |
|------|------|------|
| `workspace/input/` | 只读 | 调度器放置文件，Agent 不修改 |
| `workspace/<中间目录>/` | 读写 | SKILL 输出的中间产物 |
| `workspace/summary/` | 读写 | 最终输出，供调度器/下游读取 |

### 5.3 生命周期

1. **调度器**将文件放入 `workspace/input/`
2. **Agent** 执行流程，产出写入 `workspace/summary/`
3. **调度器**读取 `workspace/summary/manifest.json` 获取结果
4. 下游 Agent 可读取 `workspace/summary/` 下的结构化输出

---

## 6. 调度器（AGENTS.md）对接规范

### 6.1 调度流程

```
用户需求 → AGENTS.md 匹配 Agent → 加载 AGENT.md → 执行流程 → 读取 manifest.json
```

### 6.2 调度器需要做的

1. 根据 `description` 字段匹配合适的 Agent
2. 将用户文件复制到 Agent 的 `workspace/input/`
3. 加载 AGENT.md 作为执行配置
4. 等待执行完成
5. 读取 `workspace/summary/manifest.json`
6. 根据 `status` 判断是否成功
7. 将结果传递给下游 Agent 或返回给用户

### 6.3 错误处理

调度器应检查 `manifest.json` 中的 `status` 字段：

| status | 处理方式 |
|--------|----------|
| `completed` | 读取 `documents` 数组获取各文件结果 |
| `failed` | 读取 `documents[].error` 获取失败原因，决定是否重试 |
| `empty` | 告知用户无匹配文件 |

---

## 7. 知识库输出规范

本项目的目标是生成**结构化知识库**（JSON/YAML），供 AI 通过 Agent 调用和使用。

### 7.1 知识库结构

```
knowledge-base/
├── manifest.json              # 知识库索引
├── documents/
│   ├── <doc1>/
│   │   ├── content.json       # 原始内容
│   │   ├── summary.json       # 结构化总结
│   │   └── summary.md         # 可读总结
│   └── <doc2>/
│       └── ...
├── images/
│   ├── <doc1>/
│   │   ├── image_1.png
│   │   └── image_1.json       # 图片描述（结构化）
│   └── ...
└── combined/
    ├── 综合总结.json
    └── 综合总结.md
```

### 7.2 知识库 manifest.json

```json
{
  "version": "1.0",
  "generated_at": "ISO 8601",
  "document_count": 10,
  "documents": [
    {
      "id": "doc_001",
      "source_file": "report.docx",
      "title": "文档标题",
      "summary_path": "documents/report/summary.json",
      "content_path": "documents/report/content.json",
      "keywords": ["关键词1", "关键词2"],
      "language": "zh"
    }
  ]
}
```

### 7.3 知识库使用方式

下游 Agent 或 AI 助手通过以下方式使用知识库：

1. 读取 `manifest.json` 获取文档列表
2. 根据关键词/标题匹配相关文档
3. 读取 `summary.json` 获取结构化总结
4. 如需详情，读取 `content.json` 获取完整内容
5. 如需图片，读取 `images/` 目录下的图片和描述

---

## 8. 参考实现：doc-content-analysis

### 输入

```
workspace/input/
├── report1.doc
├── report2.docx
└── paper.pdf
```

### 输出

```
workspace/summary/
├── manifest.json
├── report1/
│   ├── text/
│   │   ├── content.json
│   │   ├── summary.json
│   │   └── summary.md
│   └── img/
│       ├── image_1.png
│       ├── text/image_1.txt
│       └── img-summary/image_1.md
├── report2/
│   └── text/
│       ├── content.json
│       ├── summary.json
│       └── summary.md
├── paper/
│   └── text/
│       ├── content.json
│       ├── summary.json
│       └── summary.md
├── 综合总结.json
└── 综合总结.md
```

### manifest.json 示例

```json
{
  "status": "completed",
  "total_files": 3,
  "success_count": 3,
  "failed_count": 0,
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
      "source_file": "report2.docx",
      "status": "success",
      "output_dir": "workspace/summary/report2/",
      "content_json": "workspace/summary/report2/text/content.json",
      "summary_json": "workspace/summary/report2/text/summary.json",
      "summary_md": "workspace/summary/report2/text/summary.md",
      "image_count": 0,
      "has_img_summary": false
    },
    {
      "source_file": "paper.pdf",
      "status": "success",
      "output_dir": "workspace/summary/paper/",
      "content_json": "workspace/summary/paper/text/content.json",
      "summary_json": "workspace/summary/paper/text/summary.json",
      "summary_md": "workspace/summary/paper/text/summary.md",
      "image_count": 12,
      "has_img_summary": true
    }
  ],
  "has_combined_summary": true,
  "combined_summary_json": "workspace/summary/综合总结.json",
  "combined_summary_md": "workspace/summary/综合总结.md",
  "generated_at": "2024-01-01T12:00:00"
}
```
