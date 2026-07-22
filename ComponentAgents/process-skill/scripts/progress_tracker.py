#!/usr/bin/env python3
"""
DocMind Progress Tracker（增强版）

对接 VS Code Extension 的进度显示面板：
  - 主输出：WORKSPACE/{ProjectName}/.workflow_state.json（Extension 优先读取）
  - 备份输出：WORKSPACE/.docmind-progress.json（兼容旧版 Dashboard）

特性：
  - 原子写入（先写 .tmp 再 rename）
  - 双格式同步（workflow_state + docmind-progress）
  - 事件回调（step_start / step_update / step_complete / step_fail）
  - 产物追踪（outputs）

用法：
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

  tracker.step_start(task_id, "content-extraction", message="开始提取文档")
  tracker.step_progress(task_id, "content-extraction", 50, "处理中...")
  tracker.complete_step(task_id, "content-extraction", message="完成")
  tracker.complete_task(task_id, message="知识库构建完成")
"""

import json
import os
import tempfile
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Optional


# ─────────────────────────────────────────────────────────────
# 回调函数类型
# ─────────────────────────────────────────────────────────────

StepCallback = Callable[["ProgressTracker", str, str, str, int, Optional[str]], None]
"""
回调签名: (tracker, task_id, step_id, status, progress, message) -> None
status: "pending" | "running" | "completed" | "failed" | "skipped"
"""


# ─────────────────────────────────────────────────────────────
# ProgressTracker
# ─────────────────────────────────────────────────────────────

class ProgressTracker:
    """
    DocMind 进度追踪器 — 双输出 + 原子写入 + 事件回调。

    输出文件:
      1. WORKSPACE/{project}/.workflow_state.json   (Extension 优先读取)
      2. WORKSPACE/.docmind-progress.json           (兼容旧版)
    """

    def __init__(
        self,
        root: str = "WORKSPACE",
        on_step: Optional[StepCallback] = None,
    ):
        self._root = Path(root)
        self._tasks: dict[str, dict] = {}
        self._lock = threading.Lock()
        self._on_step = on_step
        self._enable_stdout = os.environ.get("DOCMIND_STDOUT", "1") == "1"

    # ── stdout JSON 输出 ────────────────────────────────────

    def _emit(self, event: dict):
        """向 stdout 输出 JSON line（供 VS Code Extension 实时读取）"""
        if not self._enable_stdout:
            return
        try:
            import sys
            line = json.dumps(event, ensure_ascii=False, default=str)
            print(f"DOCMIND:{line}", file=sys.stdout, flush=True)
        except Exception:
            pass

    # ── 创建任务 ─────────────────────────────────────────────

    def create_task(
        self,
        project: str,
        workflow: str,
        agent: str,
        steps: list[dict],
    ) -> str:
        """
        创建新任务并在两个进度文件中初始化。

        Args:
            project: 项目名（PascalCase），如 "ChlorphenaminePaper"
            workflow: 工作流名，如 "KnowledgeBuilderWorkflow"
            agent: 当前 Agent 名
            steps: 步骤列表 [{"id": "...", "name": "..."}, ...]

        Returns:
            task_id（目前等于 project）
        """
        task_id = project
        now = self._now()

        task = {
            "task_id": task_id,
            "project": project,
            "workflow": workflow,
            "agent": agent,
            "status": "running",
            "phase": "initializing",
            "message": "任务初始化中",
            "progress": 0,
            "started_at": now,
            "updated_at": now,
            "current_step": None,
            "steps": [],
            "outputs": [],
            "error": None,
            # executor 兼容字段
            "completed_steps": [],
            "failed_steps": [],
        }

        # 初始化步骤
        for s in steps:
            task["steps"].append({
                "id": s["id"],
                "name": s["name"],
                "status": "pending",
                "percent": 0,
                "message": "",
            })

        with self._lock:
            self._tasks[task_id] = task

        self._flush(task_id)
        self._emit({"type": "task_create", "task_id": task_id, "project": project, "workflow": workflow, "agent": agent})
        return task_id

    # ── 步骤控制 ─────────────────────────────────────────────

    def step_start(self, task_id: str, step_id: str, message: str = ""):
        """标记步骤开始执行"""
        self._update_step(task_id, step_id, "running", 0, message)
        self._set_current_step(task_id, step_id)
        self._emit({"type": "step_start", "task_id": task_id, "step_id": step_id, "message": message})

    def step_progress(self, task_id: str, step_id: str, percent: int, message: str = ""):
        """更新步骤进度（0-100）"""
        self._update_step(task_id, step_id, "running", percent, message)
        self._emit({"type": "step_progress", "task_id": task_id, "step_id": step_id, "percent": percent, "message": message})

    def complete_step(self, task_id: str, step_id: str, message: str = ""):
        """标记步骤完成"""
        self._update_step(task_id, step_id, "completed", 100, message)
        with self._lock:
            task = self._tasks.get(task_id)
            if task and step_id not in task["completed_steps"]:
                task["completed_steps"].append(step_id)
        self._emit({"type": "step_complete", "task_id": task_id, "step_id": step_id, "message": message})

    def fail_step(self, task_id: str, step_id: str, error: str):
        """标记步骤失败"""
        self._update_step(task_id, step_id, "failed", 100, error)
        with self._lock:
            task = self._tasks.get(task_id)
            if task:
                task["status"] = "failed"
                task["error"] = error
                if step_id not in task["failed_steps"]:
                    task["failed_steps"].append(step_id)
        self._emit({"type": "step_fail", "task_id": task_id, "step_id": step_id, "error": error})

    def skip_step(self, task_id: str, step_id: str, reason: str = ""):
        """跳过步骤"""
        self._update_step(task_id, step_id, "skipped", 100, reason)

    # ── 任务控制 ─────────────────────────────────────────────

    def complete_task(self, task_id: str, message: str = "任务完成"):
        """标记整个任务完成"""
        with self._lock:
            task = self._tasks.get(task_id)
            if task:
                task["status"] = "completed"
                task["message"] = message
                task["progress"] = 100
                task["updated_at"] = self._now()
                task["current_step"] = None
        self._flush(task_id)
        self._emit({"type": "task_complete", "task_id": task_id, "message": message})

    def fail_task(self, task_id: str, error: str):
        """标记整个任务失败"""
        with self._lock:
            task = self._tasks.get(task_id)
            if task:
                task["status"] = "failed"
                task["error"] = error
                task["updated_at"] = self._now()
                task["current_step"] = None
        self._flush(task_id)
        self._emit({"type": "task_fail", "task_id": task_id, "error": error})

    # ── 产物追踪 ─────────────────────────────────────────────

    def add_output(self, task_id: str, label: str, path: str, kind: str = ""):
        """添加产物"""
        with self._lock:
            task = self._tasks.get(task_id)
            if task:
                # 去重
                for o in task["outputs"]:
                    if o.get("path") == path:
                        return
                task["outputs"].append({
                    "label": label,
                    "path": str(path),
                    "kind": kind,
                })
                task["updated_at"] = self._now()
        self._flush(task_id)

    # ── 状态查询 ─────────────────────────────────────────────

    def get_task(self, task_id: str) -> Optional[dict]:
        """获取任务状态快照"""
        return self._tasks.get(task_id)

    def get_status(self, task_id: str) -> str:
        """获取任务状态字符串"""
        task = self._tasks.get(task_id)
        return task["status"] if task else "unknown"

    def is_completed(self, task_id: str) -> bool:
        return self.get_status(task_id) == "completed"

    def is_failed(self, task_id: str) -> bool:
        return self.get_status(task_id) == "failed"

    # ── 内部方法 ─────────────────────────────────────────────

    def _update_step(self, task_id: str, step_id: str, status: str, percent: int, message: str):
        """更新单个步骤状态"""
        with self._lock:
            task = self._tasks.get(task_id)
            if not task:
                return

            for step in task["steps"]:
                if step["id"] == step_id:
                    step["status"] = status
                    step["percent"] = percent
                    step["message"] = message
                    break

            # 重算总进度
            total = sum(s["percent"] for s in task["steps"])
            task["progress"] = max(0, min(100, total // max(len(task["steps"]), 1)))
            task["updated_at"] = self._now()

            # 回调
            if self._on_step:
                try:
                    self._on_step(self, task_id, step_id, status, percent, message)
                except Exception:
                    pass

        self._flush(task_id)

    def _set_current_step(self, task_id: str, step_id: str):
        with self._lock:
            task = self._tasks.get(task_id)
            if task:
                task["current_step"] = step_id

    def _flush(self, task_id: str):
        """写入两个进度文件"""
        with self._lock:
            task = self._tasks.get(task_id)
            if not task:
                return

        project = task.get("project", task_id)

        # 1. 写入项目级 .workflow_state.json（Extension 优先读取）
        ws_dir = self._root / project
        ws_dir.mkdir(parents=True, exist_ok=True)
        state_path = ws_dir / ".workflow_state.json"

        state_data = {
            "project": project,
            "workflow": task.get("workflow", ""),
            "agent": task.get("agent", ""),
            "status": task["status"],
            "phase": task.get("phase", ""),
            "message": task.get("message", ""),
            "progress": task["progress"],
            "started_at": task.get("started_at", ""),
            "updated_at": task["updated_at"],
            "current_step": task.get("current_step"),
            "completed_steps": task.get("completed_steps", []),
            "failed_steps": task.get("failed_steps", []),
            "steps": task.get("steps", []),
            "outputs": task.get("outputs", []),
            "error": task.get("error"),
        }
        self._atomic_write(state_path, state_data)

        # 2. 写入全局 .docmind-progress.json（兼容旧版 Dashboard）
        global_path = self._root / ".docmind-progress.json"
        global_data = {
            "version": "1.0",
            "project": project,
            "workflow": task.get("workflow", ""),
            "agent": task.get("agent", ""),
            "status": task["status"],
            "phase": task.get("phase", ""),
            "message": task.get("message", ""),
            "progress": task["progress"],
            "started_at": task.get("started_at", ""),
            "updated_at": task["updated_at"],
            "current_step": task.get("current_step"),
            "steps": task.get("steps", []),
            "outputs": task.get("outputs", []),
            "error": task.get("error"),
        }
        self._atomic_write(global_path, global_data)

    def _atomic_write(self, path: Path, data: dict):
        """原子写入：先写临时文件，再 rename"""
        try:
            # 确保目录存在
            path.parent.mkdir(parents=True, exist_ok=True)

            # 写入临时文件
            fd, tmp_path = tempfile.mkstemp(
                suffix=".json",
                prefix=".docmind_tmp_",
                dir=str(path.parent),
            )
            try:
                with os.fdopen(fd, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                # 原子替换
                os.replace(tmp_path, str(path))
            except Exception:
                # 清理临时文件
                try:
                    os.unlink(tmp_path)
                except OSError:
                    pass
                raise
        except Exception as e:
            print(f"[ProgressTracker] Failed to write {path}: {e}", flush=True)

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()


# ─────────────────────────────────────────────────────────────
# 便捷 API（兼容旧版调用方式）
# ─────────────────────────────────────────────────────────────

# 全局单例
_global_tracker: Optional[ProgressTracker] = None


def get_tracker(root: str = "WORKSPACE") -> ProgressTracker:
    """
    获取全局 ProgressTracker 实例。

    Args:
        root: 工作区根目录，默认 "WORKSPACE"
    """
    global _global_tracker
    if _global_tracker is None:
        _global_tracker = ProgressTracker(root=root)
    return _global_tracker


# ─────────────────────────────────────────────────────────────
# 独立运行测试
# ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import time

    tracker = ProgressTracker(root="WORKSPACE")

    task_id = tracker.create_task(
        project="TestProject",
        workflow="KnowledgeBuilderWorkflow",
        agent="doc-content-analysis",
        steps=[
            {"id": "workspace-init", "name": "创建项目工作区"},
            {"id": "content-extraction", "name": "文档内容提取"},
            {"id": "knowledge-build", "name": "知识库构建"},
        ]
    )

    tracker.step_start(task_id, "workspace-init")
    time.sleep(0.5)
    tracker.complete_step(task_id, "workspace-init", "工作区已创建")

    tracker.step_start(task_id, "content-extraction")
    for p in [20, 40, 60, 80]:
        time.sleep(0.3)
        tracker.step_progress(task_id, "content-extraction", p, f"处理中 {p}%")

    tracker.complete_step(task_id, "content-extraction", "文档提取完成")
    tracker.add_output(task_id, "内容摘要", "WORKSPACE/TestProject/doc-content-analysis/summary/综合总结.json", "json")

    tracker.step_start(task_id, "knowledge-build")
    time.sleep(0.5)
    tracker.complete_step(task_id, "knowledge-build", "知识库已构建")

    tracker.complete_task(task_id, "知识库构建完成")

    print("Done! Check WORKSPACE/TestProject/.workflow_state.json and WORKSPACE/.docmind-progress.json")
