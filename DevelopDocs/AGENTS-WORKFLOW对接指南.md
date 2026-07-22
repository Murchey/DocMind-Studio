# AGENTS & WORKFLOW 对接指南

> 本文档为外部开发者提供完整的 Agent/Workflow 对接规范，包括架构、模板、工作区约定、知识库集成和项目导入导出。

---

## 目录

1. [架构总览](#1-架构总览)
2. [AGENT.md 模板](#2-agentmd-模板)
3. [SKILL.md 模板](#3-skillmd-模板)
4. [工作区约定](#4-工作区约定)
5. [进度同步（stdout JSON）](#5-进度同步stdout-json)
6. [知识库集成](#6-知识库集成)
7. [项目导入导出（.dms）](#7-项目导入导出dms)
8. [工作区文件对照表](#8-工作区文件对照表)
9. [开发检查清单](#9-开发检查清单)

---

## 1. 架构总览

### 系统架构

```
AGENTS.md（调度器）
  ├── 工作区初始化
  ├── ProgressTracker 进度追踪
  ├── Agent 调度 & 数据传递
  └── Workflows/ 配置驱动

ComponentAgents/（Agent 代码，只读）
  ├── doc-content-analysis/
  ├── doc-form-master-main/
  ├── excel-master-main/
  ├── ppt-deep-summary/
  ├── ppt-master-main/       ← 从 GitHub 下载
  ├── phd-research-agent/
  └── ppt-continuation-tool/

WORKSPACE/{ProjectName}/（运行时数据，按项目隔离）
  ├── doc-content-analysis/
  ├── doc-form-master/
  ├── excel-master/
  ├── knowledge-base/
  └── ...
```

### 核心原则

1. **职责单一**：每个 Agent 只做一件事
2. **调度器协调**：Agent 间不直接调用，通过调度器传递数据
3. **工作区隔离**：代码在 `ComponentAgents/`，数据在 `WORKSPACE/{ProjectName}/`
4. **进度可追踪**：通过 stdout JSON 实时推送进度到 VS Code 插件

### 数据流

```
用户文档 → 放入 input/
    ↓
Agent 处理 → 输出到 output/ 或 summary/
    ↓
调度器读取 manifest.json → 传递到下游 Agent
    ↓
最终输出 → output/ 或 knowledge-base/
```

---

## 2. AGENT.md 模板

每个 Agent 必须在根目录包含 `AGENT.md`：

```markdown
---
name: my-agent
version: 1.0.0
description: Agent 功能描述
tools: [python, markdown]
workspace:
  required_dirs: [input, output]
  optional_dirs: [parsed, validated, summary]
progress:
  tracking: true
  output_dir: WORKSPACE/{ProjectName}/my-agent/output
  summary_dir: WORKSPACE/{ProjectName}/my-agent/summary
---

# My Agent

## 功能说明
简要描述 Agent 的功能。

## 工作流程

### Step 1: 读取输入
- 读取 `input/` 目录下的文件

### Step 2: 处理
- 执行核心逻辑

### Step 3: 输出
- 结果写入 `output/`
- 生成 `summary/manifest.json`

## 输出格式
说明输出文件的格式和结构。

## 注意事项
- 输入文件为只读
- 输出写入工作区对应子目录
```

### 关键字段说明

| 字段 | 必需 | 说明 |
|------|------|------|
| `name` | 是 | Agent 唯一标识，与目录名一致 |
| `version` | 是 | 语义化版本号 |
| `description` | 是 | 一句话功能描述 |
| `tools` | 是 | 依赖的工具类型 |
| `workspace.required_dirs` | 是 | 必须创建的子目录 |
| `workspace.optional_dirs` | 否 | 可选子目录 |
| `progress.tracking` | 否 | 是否启用进度追踪 |

---

## 3. SKILL.md 模板

SKILL 是 Agent 内部的能力单元，放在 `SKILLS/<skill-name>/SKILL.md`：

```markdown
---
name: my-skill
version: 1.0.0
description: Skill 功能描述
tools: [python]
input:
  - type: file
    format: [docx, pdf]
    location: input/
output:
  - type: file
    format: json
    location: output/
---

# My Skill

## 功能说明
简要描述。

## 使用方法

```bash
python scripts/my_script.py input_file.docx output_dir/
```

## 输入输出

| 类型 | 格式 | 说明 |
|------|------|------|
| 输入 | DOCX/PDF | 待处理文档 |
| 输出 | JSON | 结构化结果 |

## 注意事项
- 依赖：python-docx, lxml
```

### Script 脚本规范

放在 `SKILLS/<skill-name>/scripts/` 下：

```python
#!/usr/bin/env python3
"""脚本功能说明"""

import argparse
from pathlib import Path


def process(input_path: Path, output_dir: Path):
    """核心处理逻辑"""
    output_dir.mkdir(parents=True, exist_ok=True)
    # ... 处理逻辑
    return {"status": "success", "output": str(output_dir / "result.json")}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input", help="输入文件路径")
    parser.add_argument("output", help="输出目录")
    args = parser.parse_args()

    result = process(Path(args.input), Path(args.output))
    print(result)


if __name__ == "__main__":
    main()
```

---

## 4. 工作区约定

### 目录结构

所有 Agent 的工作数据放在 `WORKSPACE/{ProjectName}/` 下，按 Agent 名称隔离：

```
WORKSPACE/{ProjectName}/
├── doc-content-analysis/
│   ├── input/          # 原始文档（只读）
│   ├── converted/      # 转换中间产物
│   └── summary/        # 提取结果
│       ├── manifest.json
│       └── <doc>/text/
├── doc-form-master/
│   ├── input/
│   ├── output/         # 格式化文档
│   ├── parsed/         # 解析结果
│   └── validated/      # 验证结果
├── excel-master/
│   ├── input/
│   ├── parsed/         # 约束解析
│   ├── solution/       # 求解结果
│   └── output/         # 最终 Excel
├── ppt-master/
│   ├── input/
│   ├── projects/<name>/exports/
│   └── output/
├── phd-research-agent/
│   ├── input/
│   └── summary/
├── knowledge-base/     # 项目级知识库
└── .workflow_state.json
```

### 命名规则

| 项目 | 规则 | 示例 |
|------|------|------|
| ProjectName | PascalCase | `氯苯那敏论文` → `ChlorphenaminePaper` |
| AgentName | 短横线连接 | `doc-form-master` |

### 调度器职责

1. 创建 `WORKSPACE/{ProjectName}/` 及 Agent 子目录
2. 复制用户文档到 `input/`
3. 初始化 ProgressTracker
4. 调用 Agent，传入工作区绝对路径
5. 检查 `manifest.json` 判断 Agent 状态
6. 传递输出到下游 Agent
7. 标记任务完成

---

## 5. 进度同步（stdout JSON）

### 机制

Python ProgressTracker 在每次状态变更时输出 `DOCMIND:{json}` 到 stdout：

```python
from progress_tracker import ProgressTracker

tracker = ProgressTracker(root="WORKSPACE")
task_id = tracker.create_task(project="MyProject", workflow="MyWorkflow", agent="my-agent",
    steps=[{"id": "step-1", "name": "处理中"}])

tracker.step_start(task_id, "step-1", "开始处理")
# stdout: DOCMIND:{"type":"step_start","task_id":"...","step_id":"step-1","message":"开始处理"}

tracker.step_progress(task_id, "step-1", 50, "处理中...")
# stdout: DOCMIND:{"type":"step_progress","task_id":"...","step_id":"step-1","percent":50}

tracker.complete_step(task_id, "step-1", "处理完成")
# stdout: DOCMIND:{"type":"step_complete","task_id":"...","step_id":"step-1","message":"处理完成"}

tracker.complete_task(task_id, "全部完成")
# stdout: DOCMIND:{"type":"task_complete","task_id":"...","message":"全部完成"}
```

### 事件类型

| type | 说明 | 必需字段 |
|------|------|----------|
| `task_create` | 任务创建 | `task_id`, `project`, `workflow`, `agent` |
| `step_start` | 步骤开始 | `task_id`, `step_id`, `message` |
| `step_progress` | 步骤进度 | `task_id`, `step_id`, `percent` |
| `step_complete` | 步骤完成 | `task_id`, `step_id`, `message` |
| `step_fail` | 步骤失败 | `task_id`, `step_id`, `error` |
| `task_complete` | 任务完成 | `task_id`, `message` |
| `task_fail` | 任务失败 | `task_id`, `error` |

### Extension 集成

VS Code 插件通过 `ProgressService` spawn Python 进程并监听 stdout：

```typescript
// 启动任务
vscode.commands.executeCommand('docmind.startTask', {
    taskId: 'my-task',
    script: 'path/to/script.py',
    args: ['arg1'],
    cwd: 'path/to/workspace'
});

// 监听进度事件
progressService.onProgress((event, task) => {
    // task 包含完整的进度状态
    console.log(`${task.project}: ${task.percent}% - ${task.currentStep}`);
});
```

### 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `DOCMIND_STDOUT` | `1` | 启用 stdout JSON 输出（设为 `0` 关闭） |
| `PYTHONUNBUFFERED` | - | 建议设为 `1`，确保输出不被缓冲 |

---

## 6. 知识库集成

### 跨 Agent 注册

任意 Agent 完成任务后，可将输出注册到项目级知识库：

```bash
python kb_manager.py register \
  WORKSPACE/{ProjectName}/knowledge-base/ \
  my-agent \
  WORKSPACE/{ProjectName}/my-agent/summary/manifest.json \
  --summary-dir WORKSPACE/{ProjectName}/my-agent/summary/
```

### kb_manager.py 命令

| 命令 | 用途 | 说明 |
|------|------|------|
| `init` | 首次构建 | 全量构建知识库 |
| `update` | 增量更新 | 基于 content_hash 对比差异 |
| `register` | 跨 Agent 注册 | 任意 Agent 注册输出到知识库 |
| `status` | 查看状态 | 显示文档数、关键词数等 |
| `query` | 查询 | 按关键词/实体/文档/关系检索 |

### manifest.json 规范

Agent 输出必须包含 `manifest.json`：

```json
{
  "status": "completed",
  "total_files": 3,
  "success_count": 3,
  "failed_count": 0,
  "documents": [
    {
      "source_file": "input.docx",
      "status": "success",
      "output_dir": "WORKSPACE/{Project}/my-agent/output/",
      "summary_json": "WORKSPACE/{Project}/my-agent/summary/doc/text/summary.json",
      "summary_md": "WORKSPACE/{Project}/my-agent/summary/doc/text/summary.md"
    }
  ]
}
```

---

## 7. 项目导入导出（.dms）

### .dms 文件格式

`.dms` 是 ZIP 压缩包（扩展名改为 `.dms`），包含：

```
项目名.dms
├── project_manifest.json    # 项目元数据
├── doc-content-analysis/
├── doc-form-master/
├── knowledge-base/
└── ...
```

### project_manifest.json

```json
{
  "format_version": "1.0",
  "exported_at": "2026-07-21T17:30:00Z",
  "source": "DocMind-Studio",
  "project_name": "ChlorphenaminePaper",
  "scope": "full",
  "agents": [
    {"name": "doc-content-analysis", "folders": ["input", "converted", "summary"], "artifact_count": 12}
  ],
  "total_files": 45,
  "total_size_bytes": 2048576
}
```

### 导出范围

| scope | 打包内容 | 典型场景 |
|-------|---------|---------|
| `full` | 整个项目目录 | 完整迁移 |
| `output-only` | 仅 output/summary | 仅分享成果 |
| `custom` | 用户选择的 Agent | 部分分享 |

### 导入流程

1. 读取 `project_manifest.json`
2. 检查同名冲突（Overwrite / Rename / Cancel）
3. 解压到 `WORKSPACE/{project_name}/`
4. 刷新 Dashboard

### 排除规则

导出时自动排除：`.workflow_state.json`、`.docmind-progress.json`、`.kb_state.json`、以 `.` 开头的文件、`*.tmp`

---

## 8. 工作区文件对照表

### 根目录

| 文件 | 作用 |
|------|------|
| `AGENTS.md` | 调度器主文件，定义所有 Agent 的调度规则 |
| `PROJECT_GUIDANCE.MD` | 从 0 部署指南 |
| `README_CN.MD` | 中文说明 |
| `README.MD` | 英文说明 |

### ComponentAgents/

| Agent | 说明 |
|-------|------|
| `doc-content-analysis` | 文档内容提取（DOC/DOCX/PDF → JSON + MD） |
| `doc-form-master-main` | 文档格式化 + AI 格式检查 |
| `excel-master-main` | Excel 处理、排课、数据对比 |
| `ppt-deep-summary` | PPT 内容深度总结 |
| `ppt-master-main` | PPT 生成（从 GitHub 下载） |
| `phd-research-agent` | 论文辅助（审阅/开题/Introduction） |
| `ppt-continuation-tool` | PPT 续写 |
| `process-skill` | 进度追踪器（ProgressTracker） |

### Workflows/

| 文件 | 工作流 |
|------|--------|
| `KnowledgeBuilderWorkflow.md` | 知识库构建 |
| `AcdamicDocsWorkflow.md` | 学术文档处理 |
| `EnterpriseDocsWorkflow.md` | 企业文档处理 |
| `CompetitionWorkflow.md` | 竞赛资源处理 |

### DevelopDocs/

| 文件 | 说明 |
|------|------|
| `AGENTS-WORKFLOW对接指南.md` | 本文档 |
| `工作区文件作用对照表.md` | 文件详细说明（旧版） |
| `知识库构建标准.md` | 知识库字段规范 |
| `项目导入导出规范.md` | .dms 格式详细规范 |

---

## 9. 开发检查清单

### 新建 Agent

- [ ] 在 `ComponentAgents/` 下创建目录
- [ ] 编写 `AGENT.md`（name/version/description/workspace/progress）
- [ ] 创建 `requirements.txt`
- [ ] 实现 SKILL 脚本（`SKILLS/<name>/scripts/`）
- [ ] 脚本输出到 `WORKSPACE/{ProjectName}/<agent>/output` 或 `summary`
- [ ] 生成 `manifest.json`（status/documents 字段）

### 进度对接

- [ ] 在脚本中导入 `ProgressTracker`
- [ ] `create_task()` 时定义 steps
- [ ] 每个 Step 前后调用 `step_start()` / `complete_step()`
- [ ] 任务完成调用 `complete_task()`
- [ ] 运行时设置 `PYTHONUNBUFFERED=1`

### 知识库对接

- [ ] 输出 `summary/manifest.json`
- [ ] manifest 包含 `status`、`documents` 字段
- [ ] 每个 document 包含 `summary_json` 和 `summary_md`
- [ ] 调度器中添加 `kb_manager.py register` 调用

### 导出兼容

- [ ] 输出目录结构符合工作区约定
- [ ] 不依赖绝对路径（使用相对路径或环境变量）
- [ ] 不写入临时文件到工作区根目录
