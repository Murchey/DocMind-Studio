# Agent 开发指南

> 本文档是 DocMind-Studio 项目中 Agent 开发的完整指南，包含设计规范和快速对接流程。

---

## 目录

1. [架构总览](#1-架构总览)
2. [快速检查清单](#2-快速检查清单)
3. [AGENT.md 规范](#3-agentmd-规范)
4. [SKILL.MD 规范](#4-skillmd-规范)
5. [输出契约规范](#5-输出契约规范)
6. [工作区规范](#6-工作区规范)
7. [新增 Agent 流程](#7-新增-agent-流程)
8. [修改 Agent 流程](#8-修改-agent-流程)
9. [调度器对接](#9-调度器对接)

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

## 2. 快速检查清单

新增或修改 Agent 时，按此清单逐项完成：

| 步骤 | 文件/位置 | 操作 | 完成 |
|------|-----------|------|------|
| 1 | `ComponentAgents/<agent>/AGENT.md` | 创建/修改 Agent 定义 | ☐ |
| 2 | `ComponentAgents/<agent>/SKILLS/<skill>/SKILL.MD` | 创建/修改 Skill 定义 | ☐ |
| 3 | `ComponentAgents/<agent>/SKILLS/<skill>/scripts/*.py` | 创建/修改脚本（脚本型 Skill） | ☐ |
| 4 | `AGENTS.md` | 更新 Agent 目录表 | ☐ |
| 5 | `AGENTS.md` | 更新目录结构（如需） | ☐ |
| 6 | `DevelopDocs/工作区文件作用对照表.md` | 添加 Agent 文件说明 | ☐ |
| 7 | `DevelopDocs/知识库构建标准.md` | 添加输入输出规范（如需） | ☐ |
| 8 | `Workflows/*.md` | 更新工作流（如需） | ☐ |

---

## 3. AGENT.md 规范

### 3.1 Front Matter（必须）

```yaml
---
name: <agent-name>                    # Agent 唯一标识
description: <一句话描述>               # 调度器用于匹配用户需求
tools: [python]                       # 依赖的工具
input: <输入路径和格式说明>              # 调度器写入数据的位置
output: <输出路径和格式说明>             # 调度器/下游 Agent 读取结果的位置
---
```

### 3.2 多 Agent 集成契约（必须）

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

### 3.3 工作区规则（必须）

```markdown
# 工作区规则

**工作区路径**：`WORKSPACE/{ProjectName}/<agent-name>/`

**目录结构**：
```
WORKSPACE/{ProjectName}/<agent-name>/
├── input/                  # 输入（只读，调度器放置）
├── <中间目录>/             # 中间产物（可选）
└── output/ 或 summary/    # 最终输出
```

**约束**：
- 工作区是 SKILL 输出的唯一存放位置
- `input/` 只读，Agent 不修改
- 每次任务开始时清空非 input 目录
```

### 3.4 执行流程（必须）

每个 Step 必须包含：
- **目的**：这一步做什么
- **调用的 SKILL**：读取哪个 SKILL.MD
- **代码示例**：如何调用 SKILL 脚本
- **输出位置**：结果写入哪里

### 3.5 核心规则（必须）

```markdown
# 核心规则

## 处理规则
1. 严格按照 SKILL.MD 中定义的步骤执行
2. ...

## 输出规则
1. JSON 格式使用 `indent=2` 格式化
2. 包含 `source_file` 字段（可追溯）
3. 包含 `generated_at` 字段（ISO 8601 时间戳）
4. 使用 UTF-8 编码

## 错误处理
1. 输入文件不存在 → 返回 `status: "empty"`
2. ...
```

### 3.6 AGENT.md 模板

```markdown
---
name: <agent-name>
description: <一句话描述，调度器用于匹配用户需求>
tools: [python]
input: WORKSPACE/{ProjectName}/<agent-name>/input/（输入说明）
output: WORKSPACE/{ProjectName}/<agent-name>/output/（输出说明）
---

# <Agent 名称>

<Agent 功能描述>

**核心原则**：<核心设计理念>

**工作区约定**：本 AGENT 的工作目录由调度器（AGENTS.md）创建，路径为 `WORKSPACE/{ProjectName}/<agent-name>/`。下文以 `{workspace}` 表示此路径。

---

## 多 Agent 集成契约

### 调用接口
调度器通过读取本 AGENT.md 并执行工作流来触发本 Agent。调度器负责创建工作区并将工作区路径传入。

### 输入契约
- 路径：`{workspace}/input/`
- 格式：<输入格式说明>
- 命名规范：<命名规则>

### 输出契约
- 路径：`{workspace}/output/` 或 `{workspace}/summary/`
- 格式：<输出格式说明>
- 核心输出：<主要输出文件>

---

## 工作区规则

**工作区路径**：由调度器创建并传入，位于 `WORKSPACE/{ProjectName}/<agent-name>/`

**目录结构**：
```
WORKSPACE/{ProjectName}/<agent-name>/
├── input/                  # 输入（只读，调度器放置）
├── <中间目录>/             # 中间产物（可选）
└── output/                 # 最终输出
    └── ...
```

**约束**：
- 工作区是 SKILL 输出的唯一存放位置
- `input/` 只读，Agent 不修改
- 每次任务开始时清空非 input 目录

---

## 执行流程

### Step 1: <步骤名称>
- **目的**：<做什么>
- **调用的 SKILL**：`<skill-name>`
- **代码示例**：
  ```python
  import sys
  sys.path.insert(0, 'SKILLS/<skill-name>/scripts')
  from <module> import <Class>
  
  instance = <Class>()
  result = instance.method('{workspace}/input/...')
  ```
- **输出位置**：`{workspace}/<目录>/`

### Step 2: <步骤名称>
...

---

## 核心规则

### 处理规则
1. 严格按照 SKILL.MD 中定义的步骤执行
2. ...

### 输出规则
1. JSON 格式使用 `indent=2` 格式化
2. 包含 `source_file` 字段（可追溯）
3. 包含 `generated_at` 字段（ISO 8601 时间戳）
4. 使用 UTF-8 编码

### 错误处理
1. 输入文件不存在 → 返回 `status: "empty"`
2. ...

---

## 可用 SKILLS

| SKILL | 功能 | 触发条件 |
|-------|------|----------|
| <skill-name> | <功能描述> | <触发条件> |

---

## 输出示例

### manifest.json
```json
{
  "status": "completed",
  "total_files": 1,
  "success_count": 1,
  "failed_count": 0,
  "documents": [
    {
      "source_file": "input.md",
      "status": "success",
      "output_dir": "{workspace}/output/",
      "result_json": "{workspace}/output/result.json",
      "result_md": "{workspace}/output/result.md"
    }
  ],
  "generated_at": "2026-06-09T12:00:00"
}
```
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

### 4.5 SKILL.MD 模板

```markdown
---
name: <skill-name>
description: <一句话描述>
tools: [python]
---

# <Skill 名称>

## 功能说明

<详细功能描述>

## 输入/输出

**输入**：
- `<输入路径>`：<输入说明>

**输出**：
- `<输出路径>`：<输出说明>

## 调用方式

```python
import sys
sys.path.insert(0, 'SKILLS/<skill-name>/scripts')
from <module> import <Class>

instance = <Class>()
result = instance.method('<input_path>')
```

```bash
python SKILLS/<skill-name>/scripts/<script>.py <input_path> [--output <output_path>]
```

## 方法参考

| 方法 | 说明 |
|------|------|
| `method1()` | 功能描述 |
| `method2()` | 功能描述 |

## 输出 JSON 结构

```json
{
  "source_file": "input.md",
  "generated_at": "2026-06-09T12:00:00",
  ...
}
```

## 错误处理

- 输入文件不存在 → 返回错误信息
- ...
```

---

## 5. 输出契约规范

### 5.1 manifest.json（必须）

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

### 5.2 结构化输出 JSON（必须）

每个 Agent 的核心输出必须同时提供：
- **JSON 格式**：供下游 Agent 程序化消费
- **MD 格式**：供人类阅读

JSON 结构由各 Agent 自行定义，但必须遵循：
- 包含 `source_file` 字段（可追溯）
- 包含 `generated_at` 字段（时间戳）
- 包含 `document_type` 字段（文档类型：`knowledge` | `requirement`）
- 使用 UTF-8 编码
- 使用 `indent=2` 格式化

### 5.3 需求文档输出规范

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

---

## 6. 工作区规范

### 6.1 路径规范

所有 Agent 的工作目录统一在根目录下 `WORKSPACE/` 中，按项目和 Agent 隔离。

```
WORKSPACE/{ProjectName}/<agent-name>/
├── input/                  # 输入（只读，调度器放置）
├── <中间产物目录>/          # SKILL 产出的中间文件
└── summary/ 或 output/    # 最终输出
    ├── manifest.json       # 处理清单（调度器入口）
    ├── <项目1>/
    │   └── <输出文件>       # 结构化 JSON + 可读 MD
    └── 综合总结.json        # 跨项目综合（可选）
```

### 6.2 目录权限

| 目录 | 权限 | 说明 |
|------|------|------|
| `input/` | 只读 | 调度器放置文件，Agent 不修改 |
| `<中间目录>/` | 读写 | SKILL 输出的中间产物 |
| `summary/` 或 `output/` | 读写 | 最终输出，供调度器/下游读取 |

### 6.3 生命周期

1. **调度器**将文件放入 `input/`
2. **Agent** 执行流程，产出写入 `summary/` 或 `output/`
3. **调度器**读取 `manifest.json` 获取结果
4. 下游 Agent 可读取结构化输出

---

## 7. 新增 Agent 流程

### 7.1 目录结构

```
ComponentAgents/<agent-name>/
├── AGENT.md                          # Agent 定义（必须）
├── README.md                         # 说明文档（可选）
└── SKILLS/
    └── <skill-name>/
        ├── SKILL.MD                  # Skill 定义（必须）
        └── scripts/
            └── <script>.py           # 脚本（脚本型 Skill 必须）
```

### 7.2 创建步骤

1. **创建目录结构**
   ```bash
   mkdir -p ComponentAgents/<agent-name>/SKILLS/<skill-name>/scripts
   ```

2. **创建 AGENT.md**（使用 3.6 节模板）

3. **创建 SKILL.MD**（使用 4.5 节模板）

4. **创建脚本**（脚本型 Skill）

5. **更新 AGENTS.md**
   - 在 `AGENT 目录` 表格中添加新 Agent
   - 在 `目录结构` 中添加新目录

6. **更新工作区文件作用对照表**
   - 添加 Agent 文件说明

7. **更新知识库构建标准**（如需）
   - 添加输入输出规范

---

## 8. 修改 Agent 流程

### 8.1 修改检查清单

| 修改类型 | 需要更新的文件 |
|----------|----------------|
| 修改 Agent 功能 | AGENT.md、可能需要更新 AGENTS.md |
| 修改 Skill 功能 | SKILL.MD、scripts/*.py |
| 新增 Skill | 新增 SKILL.MD 和 scripts/，更新 AGENT.md |
| 修改输出格式 | AGENT.md、SKILL.MD、知识库构建标准.md |
| 修改工作区结构 | AGENT.md、工作区文件作用对照表.md |

---

## 9. 调度器对接

### 9.1 调度流程

```
用户需求 → AGENTS.md 匹配 Agent → 加载 AGENT.md → 执行流程 → 读取 manifest.json
```

### 9.2 调度器职责

1. 根据 `description` 字段匹配合适的 Agent
2. 将用户文件复制到 Agent 的 `input/`
3. 加载 AGENT.md 作为执行配置
4. 等待执行完成
5. 读取 `manifest.json`
6. 根据 `status` 判断是否成功
7. 将结果传递给下游 Agent 或返回给用户

### 9.3 错误处理

| status | 处理方式 |
|--------|----------|
| `completed` | 读取 `documents` 数组获取各文件结果 |
| `failed` | 读取 `documents[].error` 获取失败原因，决定是否重试 |
| `empty` | 告知用户无匹配文件 |
