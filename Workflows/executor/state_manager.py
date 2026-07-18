"""
工作流状态管理器
Workflow State Manager

负责跟踪工作流执行状态、保存中间结果
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime


class StateManager:
    """工作流状态管理器"""

    def __init__(self, project_name: str, workspace_root: str = "WORKSPACE"):
        """
        初始化状态管理器
        
        Args:
            project_name: 项目名称
            workspace_root: 工作区根目录
        """
        self.project_name = project_name
        self.workspace_root = Path(workspace_root)
        self.project_ws = self.workspace_root / project_name
        self.state_file = self.project_ws / ".workflow_state.json"
        self.state: Dict[str, Any] = self._load_state()

    def _load_state(self) -> Dict[str, Any]:
        """加载或初始化状态文件"""
        if self.state_file.exists():
            try:
                with open(self.state_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        
        # 初始化新状态
        return {
            "project_name": self.project_name,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "current_step": None,
            "completed_steps": [],
            "failed_steps": [],
            "step_outputs": {},
        }

    def _save_state(self):
        """保存状态到文件"""
        self.state["updated_at"] = datetime.now().isoformat()
        self.project_ws.mkdir(parents=True, exist_ok=True)
        
        with open(self.state_file, "w", encoding="utf-8") as f:
            json.dump(self.state, f, indent=2, ensure_ascii=False)

    def set_current_step(self, step_id: str):
        """设置当前执行步骤"""
        self.state["current_step"] = step_id
        self._save_state()

    def mark_step_completed(self, step_id: str, output: Optional[Dict] = None):
        """标记步骤完成"""
        if step_id not in self.state["completed_steps"]:
            self.state["completed_steps"].append(step_id)
        
        if step_id in self.state["failed_steps"]:
            self.state["failed_steps"].remove(step_id)
        
        if output:
            self.state["step_outputs"][step_id] = output
        
        self.state["current_step"] = None
        self._save_state()

    def mark_step_failed(self, step_id: str, error: str):
        """标记步骤失败"""
        if step_id not in self.state["failed_steps"]:
            self.state["failed_steps"].append(step_id)
        
        self.state["step_outputs"][step_id] = {"error": error}
        self.state["current_step"] = None
        self._save_state()

    def get_step_output(self, step_id: str) -> Optional[Dict]:
        """获取步骤输出"""
        return self.state["step_outputs"].get(step_id)

    def is_step_completed(self, step_id: str) -> bool:
        """检查步骤是否完成"""
        return step_id in self.state["completed_steps"]

    def get_completed_steps(self) -> list:
        """获取已完成步骤列表"""
        return self.state["completed_steps"].copy()

    def get_failed_steps(self) -> list:
        """获取失败步骤列表"""
        return self.state["failed_steps"].copy()

    def reset(self):
        """重置状态"""
        self.state = {
            "project_name": self.project_name,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "current_step": None,
            "completed_steps": [],
            "failed_steps": [],
            "step_outputs": {},
        }
        self._save_state()

    def to_dict(self) -> Dict[str, Any]:
        """返回当前状态字典"""
        return self.state.copy()