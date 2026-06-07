"""
DocMind 进度追踪器

实现 DocMind 进度通知 JSON 对接规范，支持实时写入进度文件供 VS Code 插件展示。
"""

import json
import os
import sys
import uuid
import argparse
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Any


class ProgressTracker:
    """任务进度追踪器"""

    # 兼容的状态别名映射
    STATUS_ALIASES = {
        "processing": "running",
        "in_progress": "running",
        "active": "running",
        "success": "completed",
        "done": "completed",
        "ready": "completed",
        "error": "failed",
    }

    def __init__(self, progress_file: str = None):
        """
        初始化进度追踪器

        Args:
            progress_file: 进度文件路径，默认为 WORKSPACE/.docmind-progress.json
        """
        if progress_file is None:
            # 默认路径：WORKSPACE/.docmind-progress.json
            root = Path(__file__).parent.parent.parent.parent  # DocMind-Studio 根目录
            progress_file = str(root / "WORKSPACE" / ".docmind-progress.json")

        self.progress_file = Path(progress_file)
        self.progress_file.parent.mkdir(parents=True, exist_ok=True)

        # 当前任务数据
        self._tasks: Dict[str, Dict[str, Any]] = {}

    def _get_now_iso(self) -> str:
        """获取当前时间的 ISO 8601 格式"""
        tz = timezone(timedelta(hours=8))
        return datetime.now(tz).isoformat()

    def _normalize_status(self, status: str) -> str:
        """规范化状态值"""
        return self.STATUS_ALIASES.get(status, status)

    def _calculate_total_progress(self, steps: List[Dict]) -> int:
        """根据步骤进度计算总进度"""
        if not steps:
            return 0
        total = sum(step.get("progress", 0) for step in steps)
        return total // len(steps)

    def _write_atomic(self, data: Dict[str, Any]):
        """原子写入进度文件"""
        tmp_file = self.progress_file.with_suffix(".json.tmp")

        try:
            # 写入临时文件
            with open(tmp_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            # 替换原文件（原子操作）
            if os.name == "nt":  # Windows
                if self.progress_file.exists():
                    os.remove(self.progress_file)
            tmp_file.rename(self.progress_file)
        except Exception as e:
            # 清理临时文件
            if tmp_file.exists():
                tmp_file.unlink()
            raise e

    def _read_progress(self) -> Optional[Dict[str, Any]]:
        """读取当前进度文件"""
        if not self.progress_file.exists():
            return None
        try:
            with open(self.progress_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return None

    def create_task(
        self,
        project: str,
        workflow: str,
        agent: str,
        steps: List[Dict[str, str]] = None,
        progress_file: str = None,
    ) -> str:
        """
        创建新任务

        Args:
            project: 项目名称
            workflow: 工作流名称
            agent: 当前 Agent 名称
            steps: 步骤列表，每个步骤包含 id, name, agent
            progress_file: 自定义进度文件路径（可选）

        Returns:
            task_id: 任务 ID
        """
        if progress_file:
            self.progress_file = Path(progress_file)
            self.progress_file.parent.mkdir(parents=True, exist_ok=True)

        task_id = str(uuid.uuid4())[:8]
        now = self._get_now_iso()

        # 构建步骤列表
        step_list = []
        if steps:
            for i, step in enumerate(steps):
                step_list.append(
                    {
                        "id": step.get("id", f"step-{i+1}"),
                        "name": step.get("name", f"步骤 {i+1}"),
                        "agent": step.get("agent", agent),
                        "status": "pending" if i > 0 else "running",
                        "progress": 0,
                        "message": "",
                    }
                )

        # 构建进度数据
        progress_data = {
            "version": "1.0",
            "project": project,
            "workflow": workflow,
            "agent": agent,
            "status": "running",
            "phase": "initializing",
            "message": "任务初始化中",
            "progress": 0,
            "started_at": now,
            "updated_at": now,
            "current_step": step_list[0]["id"] if step_list else "",
            "steps": step_list,
            "outputs": [],
        }

        # 保存任务数据
        self._tasks[task_id] = progress_data

        # 写入文件
        self._write_atomic(progress_data)

        return task_id

    def update_progress(
        self,
        task_id: str,
        step_id: str = None,
        progress: int = None,
        message: str = None,
        phase: str = None,
    ):
        """
        更新任务进度

        Args:
            task_id: 任务 ID
            step_id: 步骤 ID（可选）
            progress: 进度值 0-100（可选）
            message: 状态消息（可选）
            phase: 当前阶段（可选）
        """
        task = self._tasks.get(task_id)
        if not task:
            # 尝试从文件读取
            task = self._read_progress()
            if not task:
                raise ValueError(f"Task {task_id} not found")
            self._tasks[task_id] = task

        now = self._get_now_iso()
        task["updated_at"] = now

        if message:
            task["message"] = message

        if phase:
            task["phase"] = phase

        # 更新步骤进度
        if step_id and task.get("steps"):
            for step in task["steps"]:
                if step["id"] == step_id:
                    if progress is not None:
                        step["progress"] = progress
                    if message:
                        step["message"] = message
                    step["status"] = "running"
                    task["current_step"] = step_id
                    break

        # 计算总进度
        if progress is not None and not step_id:
            task["progress"] = progress
        elif task.get("steps"):
            task["progress"] = self._calculate_total_progress(task["steps"])

        # 写入文件
        self._write_atomic(task)

    def complete_step(self, task_id: str, step_id: str, message: str = ""):
        """
        完成步骤

        Args:
            task_id: 任务 ID
            step_id: 步骤 ID
            message: 完成消息
        """
        task = self._tasks.get(task_id)
        if not task:
            task = self._read_progress()
            if not task:
                raise ValueError(f"Task {task_id} not found")
            self._tasks[task_id] = task

        now = self._get_now_iso()
        task["updated_at"] = now

        # 更新步骤状态
        if task.get("steps"):
            for i, step in enumerate(task["steps"]):
                if step["id"] == step_id:
                    step["status"] = "completed"
                    step["progress"] = 100
                    step["message"] = message or f"{step['name']}完成"

                    # 自动开始下一个步骤
                    if i + 1 < len(task["steps"]):
                        task["steps"][i + 1]["status"] = "running"
                        task["current_step"] = task["steps"][i + 1]["id"]
                    break

        # 计算总进度
        task["progress"] = self._calculate_total_progress(task["steps"])

        # 写入文件
        self._write_atomic(task)

    def add_output(
        self, task_id: str, label: str, path: str, kind: str = "file"
    ):
        """
        添加输出产物

        Args:
            task_id: 任务 ID
            label: 产物标签
            path: 产物路径
            kind: 产物类型（json, file, image 等）
        """
        task = self._tasks.get(task_id)
        if not task:
            task = self._read_progress()
            if not task:
                raise ValueError(f"Task {task_id} not found")
            self._tasks[task_id] = task

        task["updated_at"] = self._get_now_iso()

        if "outputs" not in task:
            task["outputs"] = []

        task["outputs"].append({"label": label, "path": path, "kind": kind})

        # 写入文件
        self._write_atomic(task)

    def complete_task(self, task_id: str, message: str = "任务完成"):
        """
        完成任务

        Args:
            task_id: 任务 ID
            message: 完成消息
        """
        task = self._tasks.get(task_id)
        if not task:
            task = self._read_progress()
            if not task:
                raise ValueError(f"Task {task_id} not found")
            self._tasks[task_id] = task

        now = self._get_now_iso()
        task["status"] = "completed"
        task["progress"] = 100
        task["message"] = message
        task["updated_at"] = now

        # 完成所有步骤
        if task.get("steps"):
            for step in task["steps"]:
                if step["status"] != "completed":
                    step["status"] = "completed"
                    step["progress"] = 100

        # 写入文件
        self._write_atomic(task)

    def fail_task(self, task_id: str, error: str):
        """
        标记任务失败

        Args:
            task_id: 任务 ID
            error: 错误信息
        """
        task = self._tasks.get(task_id)
        if not task:
            task = self._read_progress()
            if not task:
                raise ValueError(f"Task {task_id} not found")
            self._tasks[task_id] = task

        now = self._get_now_iso()
        task["status"] = "failed"
        task["error"] = error
        task["message"] = f"任务失败: {error}"
        task["updated_at"] = now

        # 标记当前运行中的步骤为失败
        if task.get("steps"):
            for step in task["steps"]:
                if step["status"] == "running":
                    step["status"] = "failed"
                    step["message"] = error

        # 写入文件
        self._write_atomic(task)

    def cancel_task(self, task_id: str, message: str = "任务已取消"):
        """
        取消任务

        Args:
            task_id: 任务 ID
            message: 取消消息
        """
        task = self._tasks.get(task_id)
        if not task:
            task = self._read_progress()
            if not task:
                raise ValueError(f"Task {task_id} not found")
            self._tasks[task_id] = task

        now = self._get_now_iso()
        task["status"] = "cancelled"
        task["message"] = message
        task["updated_at"] = now

        # 写入文件
        self._write_atomic(task)


def main():
    """命令行入口"""
    parser = argparse.ArgumentParser(description="DocMind 进度追踪器")
    subparsers = parser.add_subparsers(dest="command", help="命令")

    # create 命令
    create_parser = subparsers.add_parser("create", help="创建任务")
    create_parser.add_argument("--project", required=True, help="项目名称")
    create_parser.add_argument("--workflow", required=True, help="工作流名称")
    create_parser.add_argument("--agent", required=True, help="Agent 名称")
    create_parser.add_argument(
        "--steps", type=json.loads, default=[], help="步骤列表 JSON"
    )
    create_parser.add_argument("--progress-file", help="进度文件路径")

    # update 命令
    update_parser = subparsers.add_parser("update", help="更新进度")
    update_parser.add_argument("--task-id", required=True, help="任务 ID")
    update_parser.add_argument("--step-id", help="步骤 ID")
    update_parser.add_argument("--progress", type=int, help="进度值 0-100")
    update_parser.add_argument("--message", help="状态消息")
    update_parser.add_argument("--phase", help="当前阶段")
    update_parser.add_argument("--progress-file", help="进度文件路径")

    # complete-step 命令
    complete_step_parser = subparsers.add_parser("complete-step", help="完成步骤")
    complete_step_parser.add_argument("--task-id", required=True, help="任务 ID")
    complete_step_parser.add_argument("--step-id", required=True, help="步骤 ID")
    complete_step_parser.add_argument("--message", help="完成消息")
    complete_step_parser.add_argument("--progress-file", help="进度文件路径")

    # add-output 命令
    output_parser = subparsers.add_parser("add-output", help="添加产物")
    output_parser.add_argument("--task-id", required=True, help="任务 ID")
    output_parser.add_argument("--label", required=True, help="产物标签")
    output_parser.add_argument("--path", required=True, help="产物路径")
    output_parser.add_argument("--kind", default="file", help="产物类型")
    output_parser.add_argument("--progress-file", help="进度文件路径")

    # complete 命令
    complete_parser = subparsers.add_parser("complete", help="完成任务")
    complete_parser.add_argument("--task-id", required=True, help="任务 ID")
    complete_parser.add_argument("--message", default="任务完成", help="完成消息")
    complete_parser.add_argument("--progress-file", help="进度文件路径")

    # fail 命令
    fail_parser = subparsers.add_parser("fail", help="标记任务失败")
    fail_parser.add_argument("--task-id", required=True, help="任务 ID")
    fail_parser.add_argument("--error", required=True, help="错误信息")
    fail_parser.add_argument("--progress-file", help="进度文件路径")

    # cancel 命令
    cancel_parser = subparsers.add_parser("cancel", help="取消任务")
    cancel_parser.add_argument("--task-id", required=True, help="任务 ID")
    cancel_parser.add_argument("--message", default="任务已取消", help="取消消息")
    cancel_parser.add_argument("--progress-file", help="进度文件路径")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # 创建追踪器
    tracker = ProgressTracker(progress_file=getattr(args, "progress_file", None))

    try:
        if args.command == "create":
            task_id = tracker.create_task(
                project=args.project,
                workflow=args.workflow,
                agent=args.agent,
                steps=args.steps,
            )
            print(json.dumps({"task_id": task_id}, ensure_ascii=False))

        elif args.command == "update":
            tracker.update_progress(
                task_id=args.task_id,
                step_id=args.step_id,
                progress=args.progress,
                message=args.message,
                phase=args.phase,
            )
            print(json.dumps({"status": "ok"}, ensure_ascii=False))

        elif args.command == "complete-step":
            tracker.complete_step(
                task_id=args.task_id,
                step_id=args.step_id,
                message=args.message or "",
            )
            print(json.dumps({"status": "ok"}, ensure_ascii=False))

        elif args.command == "add-output":
            tracker.add_output(
                task_id=args.task_id,
                label=args.label,
                path=args.path,
                kind=args.kind,
            )
            print(json.dumps({"status": "ok"}, ensure_ascii=False))

        elif args.command == "complete":
            tracker.complete_task(args.task_id, message=args.message)
            print(json.dumps({"status": "ok"}, ensure_ascii=False))

        elif args.command == "fail":
            tracker.fail_task(args.task_id, error=args.error)
            print(json.dumps({"status": "ok"}, ensure_ascii=False))

        elif args.command == "cancel":
            tracker.cancel_task(args.task_id, message=args.message)
            print(json.dumps({"status": "ok"}, ensure_ascii=False))

    except Exception as e:
        print(json.dumps({"error": str(e)}, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
