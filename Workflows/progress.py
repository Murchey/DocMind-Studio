"""
DocMind Progress Bridge — Workflows/executor 与 Extension 之间的桥梁。

此模块是对 process-skill ProgressTracker 的封装，供 executor 在运行工作流时
自动上报进度到 VS Code Extension 的 Dashboard。

用法（在 executor 中）:
    from Workflows.progress import start_workflow, step_complete, workflow_done

    start_workflow("MyProject", "KnowledgeBuilderWorkflow", "doc-content-analysis",
                   steps=["workspace-init", "content-extraction", "knowledge-build"])
    step_complete("workspace-init", "工作区已创建")
    step_complete("content-extraction", "文档提取完成")
    workflow_done("知识库已构建")
"""

import sys
from pathlib import Path
from typing import Optional

# 确保能找到 process-skill
_root = Path(__file__).parent.parent
_skill_path = _root / "ComponentAgents" / "process-skill" / "scripts"
if str(_skill_path) not in sys.path:
    sys.path.insert(0, str(_skill_path))

from progress_tracker import ProgressTracker, get_tracker

__all__ = [
    "start_workflow",
    "start_step",
    "step_progress",
    "step_complete",
    "step_fail",
    "step_skip",
    "workflow_done",
    "workflow_fail",
    "add_output",
    "get_status",
    "ProgressTracker",
    "get_tracker",
]

_current_task: Optional[str] = None
_tracker: Optional[ProgressTracker] = None


def _ensure_tracker(root: str = "WORKSPACE") -> ProgressTracker:
    global _tracker
    if _tracker is None:
        _tracker = ProgressTracker(root=root)
    return _tracker


def start_workflow(
    project: str,
    workflow: str,
    agent: str,
    steps: list[str],
    root: str = "WORKSPACE",
) -> str:
    """
    开始一个工作流并在 Dashboard 中初始化进度。

    Args:
        project: 项目名
        workflow: 工作流名
        agent: 当前 Agent 名
        steps: 步骤 id 列表
        root: 工作区根目录

    Returns:
        task_id（= project）
    """
    global _current_task
    tracker = _ensure_tracker(root)
    _current_task = tracker.create_task(
        project=project,
        workflow=workflow,
        agent=agent,
        steps=[{"id": s, "name": s} for s in steps],
    )
    return _current_task


def start_step(step_id: str, message: str = ""):
    """标记步骤开始"""
    if _current_task and _tracker:
        _tracker.step_start(_current_task, step_id, message)


def step_progress(step_id: str, percent: int, message: str = ""):
    """更新步骤进度"""
    if _current_task and _tracker:
        _tracker.step_progress(_current_task, step_id, percent, message)


def step_complete(step_id: str, message: str = ""):
    """标记步骤完成"""
    if _current_task and _tracker:
        _tracker.complete_step(_current_task, step_id, message)


def step_fail(step_id: str, error: str):
    """标记步骤失败"""
    if _current_task and _tracker:
        _tracker.fail_step(_current_task, step_id, error)


def step_skip(step_id: str, reason: str = ""):
    """跳过步骤"""
    if _current_task and _tracker:
        _tracker.skip_step(_current_task, step_id, reason)


def workflow_done(message: str = "工作流执行完成"):
    """标记工作流完成"""
    if _current_task and _tracker:
        _tracker.complete_task(_current_task, message)


def workflow_fail(error: str):
    """标记工作流失败"""
    if _current_task and _tracker:
        _tracker.fail_task(_current_task, error)


def add_output(label: str, path: str, kind: str = ""):
    """添加产物到 Dashboard"""
    if _current_task and _tracker:
        _tracker.add_output(_current_task, label, path, kind)


def get_status() -> str:
    """获取当前任务状态"""
    if _current_task and _tracker:
        return _tracker.get_status(_current_task)
    return "unknown"
