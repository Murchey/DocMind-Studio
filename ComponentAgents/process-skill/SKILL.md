---
name: process-skill
description: 同步插件进度的 Skill，用于实时写入进度文件供 VS Code 插件展示
tools: [python]
---

# Process Skill

同步插件进度的 Skill，实现 DocMind 进度通知 JSON 对接规范，支持实时写入进度文件供 VS Code 插件展示。

## 功能说明

- 创建任务并初始化进度
- 更新步骤进度
- 标记步骤/任务完成
- 添加输出产物
- 标记任务失败/取消

## 输入/输出

**输入**：
- 任务信息（项目名、工作流、Agent、步骤列表）

**输出**：
- `WORKSPACE/.docmind-progress.json`：进度文件（供 VS Code 插件读取）

## 调用方式

```python
import sys
sys.path.insert(0, 'ComponentAgents/process-skill/scripts')
from progress_tracker import ProgressTracker

# 初始化
tracker = ProgressTracker()

# 创建任务
task_id = tracker.create_task(
    project="ProjectName",
    workflow="KnowledgeBuilderWorkflow",
    agent="doc-content-analysis",
    steps=[
        {"id": "step1", "name": "格式转换", "agent": "doc-content-analysis"},
        {"id": "step2", "name": "内容提取", "agent": "doc-content-analysis"},
        {"id": "step3", "name": "AI总结", "agent": "doc-content-analysis"},
    ]
)

# 更新进度
tracker.update_progress(task_id, step_id="step1", progress=50, message="正在转换...")

# 完成步骤
tracker.complete_step(task_id, "step1", message="格式转换完成")

# 添加输出产物
tracker.add_output(task_id, label="转换结果", path="workspace/converted/", kind="file")

# 完成任务
tracker.complete_task(task_id, message="所有任务完成")
```

## 命令行调用

```bash
# 创建任务
python scripts/progress_tracker.py create --project "MyProject" --workflow "KnowledgeBuilder" --agent "doc-content-analysis" --steps '[{"id":"step1","name":"格式转换"}]'

# 更新进度
python scripts/progress_tracker.py update --task-id <task_id> --step-id step1 --progress 50 --message "正在转换..."

# 完成步骤
python scripts/progress_tracker.py complete-step --task-id <task_id> --step-id step1 --message "完成"

# 完成任务
python scripts/progress_tracker.py complete --task-id <task_id> --message "任务完成"
```

## 方法参考

| 方法 | 说明 |
|------|------|
| `create_task()` | 创建新任务，返回 task_id |
| `update_progress()` | 更新步骤进度 |
| `complete_step()` | 标记步骤完成 |
| `complete_task()` | 标记任务完成 |
| `add_output()` | 添加输出产物 |
| `fail_task()` | 标记任务失败 |
| `cancel_task()` | 取消任务 |

## 进度文件结构

```json
{
  "version": "1.0",
  "project": "ProjectName",
  "workflow": "KnowledgeBuilderWorkflow",
  "agent": "doc-content-analysis",
  "status": "running",
  "phase": "content-extraction",
  "message": "正在提取文档内容...",
  "progress": 45,
  "started_at": "2026-06-09T12:00:00+08:00",
  "updated_at": "2026-06-09T12:05:00+08:00",
  "current_step": "step2",
  "steps": [
    {
      "id": "step1",
      "name": "格式转换",
      "agent": "doc-content-analysis",
      "status": "completed",
      "progress": 100,
      "message": "格式转换完成"
    },
    {
      "id": "step2",
      "name": "内容提取",
      "agent": "doc-content-analysis",
      "status": "running",
      "progress": 45,
      "message": "正在提取文档内容..."
    }
  ],
  "outputs": [
    {"label": "转换结果", "path": "workspace/converted/", "kind": "file"}
  ]
}
```
