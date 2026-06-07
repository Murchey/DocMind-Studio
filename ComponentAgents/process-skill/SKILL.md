---
name: progress-tracker
description: 任务进度追踪与通知，支持实时写入进度 JSON 文件，供 VS Code 插件展示任务状态。
tools: [python]
---

# Progress Tracker

任务进度追踪与通知 Skill。在 AGENTS 执行任务时持续写入进度 JSON 文件，供 VS Code 插件自动检测并在 Dashboard 中展示任务进度。

**核心原则**：原子写入、完整状态快照、兼容规范 Schema。

**工作区约定**：进度文件默认写入 `WORKSPACE/.docmind-progress.json`，支持自定义路径。

---

# 功能概览

```
Agent 执行任务
    ↓
ProgressTracker.update()  ←  实时更新进度
    ↓
写入 .docmind-progress.json（原子写入）
    ↓
VS Code 插件检测文件变化
    ↓
Dashboard 展示任务进度
```

---

# 调用方式

## 初始化

```python
import sys
sys.path.insert(0, 'ComponentAgents/process-skill/scripts')
from progress_tracker import ProgressTracker

# 使用默认路径（WORKSPACE/.docmind-progress.json）
tracker = ProgressTracker()

# 自定义路径
tracker = ProgressTracker(progress_file='WORKSPACE/MyProject/progress.json')
```

## 创建任务

```python
# 创建新任务，返回 task_id
task_id = tracker.create_task(
    project="ChlorphenaminePaper",
    workflow="KnowledgeBuilderWorkflow",
    agent="doc-content-analysis",
    steps=[
        {"id": "workspace-init", "name": "创建项目工作区", "agent": "AGENTS.md"},
        {"id": "content-extraction", "name": "文档内容提取", "agent": "doc-content-analysis"},
        {"id": "knowledge-build", "name": "知识库构建", "agent": "knowledge-builder"},
    ]
)
```

## 更新进度

```python
# 更新当前步骤进度
tracker.update_progress(
    task_id=task_id,
    step_id="content-extraction",
    progress=55,
    message="正在处理 氯苯那敏论文.docx"
)

# 更新总进度
tracker.update_progress(
    task_id=task_id,
    progress=42,
    message="正在提取文档正文与图片"
)
```

## 完成步骤

```python
# 标记步骤完成
tracker.complete_step(
    task_id=task_id,
    step_id="content-extraction",
    message="文档内容提取完成"
)
```

## 添加产物

```python
# 添加输出产物
tracker.add_output(
    task_id=task_id,
    label="内容摘要",
    path="WORKSPACE/ChlorphenaminePaper/doc-content-analysis/summary/综合总结.json",
    kind="json"
)
```

## 任务完成

```python
# 标记任务完成
tracker.complete_task(task_id, message="知识库构建完成")
```

## 任务失败

```python
# 标记任务失败
tracker.fail_task(task_id, error="Conversion failed: Word not installed")
```

---

# 命令行调用

```bash
# 创建任务
python ComponentAgents/process-skill/scripts/progress_tracker.py create \
  --project "ChlorphenaminePaper" \
  --workflow "KnowledgeBuilderWorkflow" \
  --agent "doc-content-analysis" \
  --steps '[{"id":"step1","name":"步骤1","agent":"agent1"}]'

# 更新进度
python ComponentAgents/process-skill/scripts/progress_tracker.py update \
  --task-id <task_id> \
  --step-id "step1" \
  --progress 50 \
  --message "处理中"

# 完成任务
python ComponentAgents/process-skill/scripts/progress_tracker.py complete \
  --task-id <task_id>

# 失败任务
python ComponentAgents/process-skill/scripts/progress_tracker.py fail \
  --task-id <task_id> \
  --error "错误信息"
```

---

# Schema 规范

进度 JSON 文件遵循 `DocMind进度通知JSON对接规范.md`：

```json
{
  "version": "1.0",
  "project": "ChlorphenaminePaper",
  "workflow": "KnowledgeBuilderWorkflow",
  "agent": "doc-content-analysis",
  "status": "running",
  "phase": "extracting",
  "message": "正在提取文档正文与图片",
  "progress": 42,
  "started_at": "2026-06-07T20:40:00+08:00",
  "updated_at": "2026-06-07T20:42:12+08:00",
  "current_step": "content-extraction",
  "steps": [...],
  "outputs": [...]
}
```

## 状态值

- `idle` - 空闲
- `pending` - 等待中
- `running` - 运行中
- `completed` - 已完成
- `failed` - 失败
- `cancelled` - 已取消

---

# 集成示例

在 AGENT 中使用：

```python
from progress_tracker import ProgressTracker

class MyAgent:
    def __init__(self, workspace_path):
        self.tracker = ProgressTracker(progress_file=f"{workspace_path}/../.docmind-progress.json")
        self.task_id = None

    def run(self, files):
        # 创建任务
        self.task_id = self.tracker.create_task(
            project="MyProject",
            workflow="MyWorkflow",
            agent="my-agent",
            steps=[
                {"id": "step1", "name": "步骤1", "agent": "my-agent"},
                {"id": "step2", "name": "步骤2", "agent": "my-agent"},
            ]
        )

        try:
            # 执行步骤1
            self.tracker.update_progress(self.task_id, "step1", 0, "开始处理")
            # ... 执行任务 ...
            self.tracker.update_progress(self.task_id, "step1", 50, "处理中")
            # ... 继续处理 ...
            self.tracker.complete_step(self.task_id, "step1", "步骤1完成")

            # 执行步骤2
            self.tracker.update_progress(self.task_id, "step2", 0, "开始步骤2")
            # ... 执行任务 ...
            self.tracker.add_output(self.task_id, "结果文件", "path/to/output.json", "json")
            self.tracker.complete_step(self.task_id, "step2", "步骤2完成")

            # 完成任务
            self.tracker.complete_task(self.task_id, "任务完成")
        except Exception as e:
            self.tracker.fail_task(self.task_id, str(e))
            raise
```
