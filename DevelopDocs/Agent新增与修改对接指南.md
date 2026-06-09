# Agent 新增与修改对接指南

本文档提供新增和修改 Agent 时的快速对接流程，确保与 DocMind-Studio 项目规范一致。

---

## 快速检查清单

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
| 8 | `DevelopDocs/Agent对接多Agent项目设计规范.md` | 更新规范（如需） | ☐ |
| 9 | `Workflows/*.md` | 更新工作流（如需） | ☐ |

---

## 一、新增 Agent

### 1.1 目录结构

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

### 1.2 创建 AGENT.md

使用以下模板：

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

### result.json
```json
{
  "source_file": "input.md",
  "generated_at": "2026-06-09T12:00:00",
  ...
}
```
```

### 1.3 创建 SKILL.MD

使用以下模板：

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

### 1.4 更新 AGENTS.md

在 `AGENT 目录` 表格中添加新 Agent：

```markdown
## AGENT 目录

| Agent | 路径 | 职责 |
|-------|------|------|
| ... | ... | ... |
| <agent-name> | `ComponentAgents/<agent-name>/AGENT.md` | <职责描述> |
```

在 `目录结构` 中添加：

```
ComponentAgents/
├── ...
└── <agent-name>/

WORKSPACE/{ProjectName}/
├── ...
└── <agent-name>/
```

### 1.5 更新工作区文件作用对照表

在 `ComponentAgents/ 目录` 章节添加：

```markdown
### 2.X <agent-name>（<中文名称>）

| 文件 | 作用 |
|------|------|
| `AGENT.md` | Agent 定义：<功能描述> |

#### SKILLS/<skill-name>（<Skill 中文名称>）

| 文件 | 作用 |
|------|------|
| `SKILL.MD` | Skill 定义：<功能描述> |
| `scripts/<script>.py` | 核心脚本：<功能描述> |
```

在 `WORKSPACE/ 目录` 章节添加：

```markdown
### 3.X <agent-name> 工作区

```
WORKSPACE/{ProjectName}/<agent-name>/
├── input/                        # 输入（只读）
│   └── *.md                      # 输入文件
└── output/                       # 最终输出
    ├── result.json               # 结构化结果
    └── result.md                 # 可读报告
```
```

---

## 二、修改现有 Agent

### 2.1 修改步骤

| 步骤 | 操作 |
|------|------|
| 1 | 读取现有 `AGENT.md` 了解当前结构 |
| 2 | 读取相关 `SKILL.MD` 了解当前能力 |
| 3 | 确定修改范围（新增 Skill / 修改现有 Skill / 修改流程） |
| 4 | 执行修改 |
| 5 | 更新相关文档 |

### 2.2 新增 Skill

1. 创建目录：`ComponentAgents/<agent>/SKILLS/<new-skill>/`
2. 创建 `SKILL.MD`
3. 创建脚本（如需）：`scripts/<script>.py`
4. 更新 `AGENT.md`：
   - 在 `可用 SKILLS` 表格中添加
   - 在 `执行流程` 中添加调用步骤

### 2.3 修改现有 Skill

1. 读取 `SKILL.MD` 了解当前接口
2. 修改脚本：`scripts/<script>.py`
3. 如接口变化，更新 `SKILL.MD`
4. 更新 `AGENT.md` 中相关说明

### 2.4 修改执行流程

1. 读取 `AGENT.md` 的 `执行流程` 章节
2. 添加/修改/删除 Step
3. 确保每个 Step 包含：目的、调用的 SKILL、代码示例、输出位置

---

## 三、需求类 Agent 特殊规范

如果 Agent 用于处理用户需求（如排课、表格分析），需要额外完成：

### 3.1 在 doc-content-analysis 中注册需求类型

修改 `ComponentAgents/doc-content-analysis/AGENT.md`，在 `Step 4.1 文档类型识别` 中添加：

```markdown
**识别规则**：
- 包含"<关键词>"等关键词 → <需求类型>
```

### 3.2 定义需求 summary.md 格式

在 `Step 4.3 需求文档总结` 中添加格式模板：

```markdown
**<需求类型>需求 summary.md 示例**：

```markdown
# <需求标题>

**来源文件**：`<原始文件名>`
**文档类型**：需求文档
**需求类型**：<需求类型>
**目标 Agent**：<agent-name>

---
...
```
```

### 3.3 更新知识库构建标准

修改 `DevelopDocs/知识库构建标准.md`，添加：

```markdown
### <agent-name> 输入

| 任务类型 | 输入文件 | 说明 |
|----------|----------|------|
| ... | ... | ... |
```

### 3.4 更新需求传递流程

修改 `Workflows/KnowledgeBuilderWorkflow.md`，在需求传递流程中添加：

```markdown
└─── <agent-name> ────┐
                      ▼
    ┌─────────────────────────────┐
    │  <agent-name>               │
    │  input: summary.md          │
    │  output: <输出说明>          │
    └─────────────────────────────┘
```

---

## 四、命名规范

| 项目 | 规则 | 示例 |
|------|------|------|
| Agent 目录名 | 小写 + 连字符 | `schedule-agent`、`doc-content-analysis` |
| Skill 目录名 | 小写 + 连字符 | `constraint-parser`、`excel_io` |
| 脚本文件名 | 小写 + 下划线 | `constraint_parser.py`、`schedule_solver.py` |
| 类名 | PascalCase | `ConstraintParser`、`ScheduleSolver` |
| 方法名 | 小写 + 下划线 | `parse()`、`solve()` |

---

## 五、依赖管理

如果 Agent 需要 Python 依赖，在 Agent 根目录创建 `requirements.txt`：

```
openpyxl>=3.0.0
pandas>=1.3.0
```

---

## 六、常见问题

### Q1: 如何确定 Agent 是脚本型还是 AI 原生型？

| 类型 | 特点 | 示例 |
|------|------|------|
| 脚本型 | 需要 Python 脚本处理数据 | doc-convertor、schedule-solver |
| AI 原生型 | 依赖 AI 能力（总结、分析） | idea-evaluator、知识库总结 |
| 混合型 | 脚本 + AI 结合 | img-reader（OCR + AI 视觉） |

### Q2: 工作区路径如何确定？

工作区路径由调度器创建，格式为：`WORKSPACE/{ProjectName}/<agent-name>/`

在 AGENT.md 中使用 `{workspace}` 占位符表示。

### Q3: 如何让 Agent 支持从知识库读取输入？

在 AGENT.md 的 `输入契约` 中说明：

```markdown
### 输入契约
- 路径：`{workspace}/input/`
- 格式：Markdown 文档（支持直接读取 doc-content-analysis 输出的知识库 MD）
```

### Q4: manifest.json 必须包含哪些字段？

```json
{
  "status": "completed | failed | empty",
  "total_files": 1,
  "success_count": 1,
  "failed_count": 0,
  "documents": [...],
  "generated_at": "ISO 8601"
}
```

---

## 七、解决 Agent 执行被打断的问题

### 7.1 问题分析

| 问题 | 原因 | 影响 |
|------|------|------|
| 多步骤切换 | 每个 Step 需要 AI 读取 SKILL.MD 再执行 | 上下文切换频繁 |
| AI 原生步骤 | 如 doc-content-analysis Step 4（AI 总结） | 大文档处理时耗时长 |
| 步骤过于分散 | 脚本步骤和 AI 步骤交替执行 | 执行效率低 |

### 7.2 解决方案：优化 AGENT.md 设计

**核心原则**：将脚本步骤合并执行，减少 AI 介入次数。

#### 设计模式 1：脚本步骤合并

**反面示例**（容易被打断）：
```markdown
## 执行流程
### Step 1: 格式转换
- 调用 doc-convertor 的 convert()

### Step 2: 内容提取
- 调用 doc-convertor 的 extract_text()

### Step 3: 图片提取
- 调用 doc-convertor 的 extract_images()
```

**正面示例**（一次性执行）：
```markdown
## 执行流程
### Step 1: 格式转换 + 内容提取 + 图片提取
- 调用 doc-convertor 的 process_all() 一键完成
- 代码示例：
  ```python
  converter.process_all('{workspace}/input/', '{workspace}/')
  ```

### Step 2: AI 总结（需要 AI 介入）
- 读取 content.json，生成 summary.json/md
```

#### 设计模式 2：脚本优先，AI 集中

```markdown
## 执行流程

### Step 1: 数据处理（脚本批量执行）
调用所有脚本型 SKILL，一次性完成数据处理：
```python
# 1. 格式转换
converter.process_all('{workspace}/input/', '{workspace}/')

# 2. 图片 OCR
reader.process_batch('{workspace}/summary/*/img/')
```

### Step 2: AI 分析（集中处理）
AI 读取所有处理结果，进行分析和总结
```

#### 设计模式 3：使用复合脚本

为 Agent 创建一个复合脚本，将多个 SKILL 脚本串联执行：

```python
# scripts/run_all.py
from doc_converter import DocConverter
from img_reader import ImgReader

def run_all(input_dir, output_dir):
    # 1. 格式转换 + 内容提取
    converter = DocConverter()
    converter.process_all(input_dir, output_dir)
    
    # 2. 图片 OCR
    reader = ImgReader()
    reader.process_batch(f'{output_dir}/summary/*/img/')
    
    return {"status": "completed"}
```

### 7.3 AGENT.md 设计规范

| 规范 | 说明 |
|------|------|
| 脚本步骤合并 | 多个脚本步骤合并为一个 Step |
| 脚本优先执行 | 脚本步骤放在前面，AI 步骤放在后面 |
| 提供复合脚本 | 为复杂流程创建一键执行脚本 |
| 减少 AI 等待 | 脚本执行期间不需要 AI 介入 |

### 7.4 使用进度追踪器同步状态

执行过程中使用 `process-skill` 同步进度到 VS Code 插件：

```python
import sys
sys.path.insert(0, 'ComponentAgents/process-skill/scripts')
from progress_tracker import ProgressTracker

tracker = ProgressTracker()

# 创建任务
task_id = tracker.create_task(
    project="MyProject",
    workflow="KnowledgeBuilderWorkflow",
    agent="doc-content-analysis",
    steps=[
        {"id": "step1", "name": "数据处理", "agent": "doc-content-analysis"},
        {"id": "step2", "name": "AI分析", "agent": "doc-content-analysis"},
    ]
)

# 执行脚本步骤
tracker.update_progress(task_id, "step1", progress=50, message="正在处理...")
converter.process_all(input_dir, output_dir)
tracker.complete_step(task_id, "step1", message="数据处理完成")

# 执行 AI 步骤
tracker.update_progress(task_id, "step2", progress=0, message="AI 分析中...")
# ... AI 处理 ...
tracker.complete_step(task_id, "step2", message="AI 分析完成")

# 完成任务
tracker.complete_task(task_id, message="任务完成")
```

---

## 八、文档更新检查表

修改 Agent 后，检查以下文档是否需要更新：

| 文档 | 更新条件 |
|------|----------|
| `AGENTS.md` | 新增 Agent、修改 Agent 描述 |
| `工作区文件作用对照表.md` | 新增 Agent、修改目录结构 |
| `知识库构建标准.md` | 修改输入输出格式、新增需求类型 |
| `Agent对接多Agent项目设计规范.md` | 修改输出契约、新增规范 |
| `Workflows/*.md` | 修改工作流、新增需求传递 |
