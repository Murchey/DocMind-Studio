---
name: process-skill
description: 进度追踪与 VS Code Extension Dashboard 对接，支持双格式输出（.workflow_state.json + .docmind-progress.json）
tools: [python]
---

# Process Skill — 进度追踪与 Extension 对接

## 功能说明

将 Agent 执行进度实时推送到 VS Code Extension 的 Dashboard 面板。

**输出文件**：
- `WORKSPACE/{ProjectName}/.workflow_state.json`（Extension 优先读取，匹配 executor 格式）
- `WORKSPACE/.docmind-progress.json`（兼容旧版）

**核心特性**：
- 原子写入（`.tmp` → `rename`，避免 Dashboard 读到半截 JSON）
- 双格式同步（两个文件同时更新）
- 事件回调（可注册 `on_step` 监听器）
- 产物追踪（`add_output`）
- `Workflows/progress.py` 桥接层（executor 可直接调用）

## 用法

### 在 Agent 中直接使用

```python
import sys
sys.path.insert(0, 'ComponentAgents/process-skill/scripts')
from progress_tracker import ProgressTracker

tracker = ProgressTracker(root="WORKSPACE")

task_id = tracker.create_task(
    project="MyProject",
    workflow="KnowledgeBuilderWorkflow",
    agent="doc-content-analysis",
    steps=[
        {"id": "workspace-init", "name": "创建项目工作区"},
        {"id": "content-extraction", "name": "文档内容提取"},
        {"id": "knowledge-build", "name": "知识库构建"},
    ]
)

tracker.step_start(task_id, "content-extraction", "开始提取文档")
tracker.step_progress(task_id, "content-extraction", 50, "处理中...")
tracker.complete_step(task_id, "content-extraction", "文档提取完成")

tracker.add_output(task_id, "内容摘要", "WORKSPACE/MyProject/doc-content-analysis/summary/综合总结.json", "json")
tracker.complete_task(task_id, "知识库构建完成")
```

### 在 Workflows/executor 中使用（桥接层）

```python
from Workflows.progress import start_workflow, step_complete, step_progress, workflow_done

start_workflow("MyProject", "KnowledgeBuilderWorkflow", "doc-content-analysis",
               steps=["workspace-init", "content-extraction", "knowledge-build"])

step_complete("workspace-init", "工作区已创建")
step_complete("content-extraction", "文档提取完成")
step_complete("knowledge-build", "知识库已构建")
workflow_done("知识库构建完成")
```

### 使用全局单例（兼容旧版）

```python
from progress_tracker import get_tracker

tracker = get_tracker("WORKSPACE")
tracker.create_task(...)
tracker.complete_step(task_id, "xxx")
```

## 输出的 .workflow_state.json 结构

```json
{
  "project": "MyProject",
  "workflow": "KnowledgeBuilderWorkflow",
  "agent": "doc-content-analysis",
  "status": "running",
  "phase": "extracting",
  "message": "正在提取文档正文",
  "progress": 42,
  "started_at": "2026-06-09T12:00:00+00:00",
  "updated_at": "2026-06-09T12:00:42+00:00",
  "current_step": "content-extraction",
  "completed_steps": ["workspace-init"],
  "failed_steps": [],
  "steps": [
    {
      "id": "workspace-init",
      "name": "创建项目工作区",
      "status": "completed",
      "percent": 100,
      "message": "工作区已创建"
    },
    {
      "id": "content-extraction",
      "name": "文档内容提取",
      "status": "running",
      "percent": 55,
      "message": "正在处理文档..."
    }
  ],
  "outputs": [
    {
      "label": "内容摘要",
      "path": "WORKSPACE/MyProject/doc-content-analysis/summary/综合总结.json",
      "kind": "json"
    }
  ],
  "error": null
}
```

## 方法参考

| 方法 | 说明 |
|------|------|
| `create_task(project, workflow, agent, steps)` | 创建任务，返回 task_id |
| `step_start(task_id, step_id, message)` | 步骤开始 |
| `step_progress(task_id, step_id, percent, message)` | 更新步骤进度 |
| `complete_step(task_id, step_id, message)` | 步骤完成 |
| `fail_step(task_id, step_id, error)` | 步骤失败 |
| `skip_step(task_id, step_id, reason)` | 跳过步骤 |
| `complete_task(task_id, message)` | 任务完成 |
| `fail_task(task_id, error)` | 任务失败 |
| `add_output(task_id, label, path, kind)` | 添加产物 |
| `get_task(task_id)` | 获取任务状态快照 |
| `get_status(task_id)` | 获取状态字符串 |
| `is_completed(task_id)` | 是否已完成 |
| `is_failed(task_id)` | 是否已失败 |

## Extension 读取流程

```
Agent 调用 ProgressTracker
    ↓ 原子写入
WORKSPACE/{ProjectName}/.workflow_state.json  ← Extension FileSystemWatcher 监听
WORKSPACE/.docmind-progress.json              ← Extension 兼容备用
    ↓ DashboardPanel.scanProgress() 读取
    ↓
Dashboard 显示进度条 + 步骤列表 + 产物链接
```

## 错误处理

- 写入失败：打印 stderr 日志，不阻断 Agent 执行
- 临时文件残留：自动清理
- Extension 离线：Agent 正常执行，进度文件在 Extension 下次打开时读取
