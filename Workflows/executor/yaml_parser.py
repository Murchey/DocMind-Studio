"""
YAML 工作流配置解析器
Workflow YAML Configuration Parser
"""

import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional


class WorkflowParser:
    """工作流 YAML 配置解析器"""

    def __init__(self, config_path: str):
        """
        初始化解析器
        
        Args:
            config_path: YAML 配置文件路径
        """
        self.config_path = Path(config_path)
        self.config: Dict[str, Any] = {}
        self._load_config()

    def _load_config(self):
        """加载 YAML 配置文件"""
        if not self.config_path.exists():
            raise FileNotFoundError(f"工作流配置文件不存在: {self.config_path}")
        
        with open(self.config_path, "r", encoding="utf-8") as f:
            self.config = yaml.safe_load(f)

    def get_workflow_name(self) -> str:
        """获取工作流名称"""
        return self.config.get("workflow", {}).get("name", "UnknownWorkflow")

    def get_workflow_description(self) -> str:
        """获取工作流描述"""
        return self.config.get("workflow", {}).get("description", "")

    def get_triggers(self) -> List[str]:
        """获取触发关键词列表"""
        triggers = self.config.get("triggers", [])
        return [t.get("keyword", "") for t in triggers if isinstance(t, dict)]

    def get_steps(self) -> List[Dict[str, Any]]:
        """获取所有步骤定义"""
        return self.config.get("steps", [])

    def get_step_by_id(self, step_id: str) -> Optional[Dict[str, Any]]:
        """根据 ID 获取步骤"""
        for step in self.get_steps():
            if step.get("id") == step_id:
                return step
        return None

    def get_dataflow(self) -> str:
        """获取数据流描述"""
        return self.config.get("dataflow", "")

    def get_status_checks(self) -> List[Dict[str, str]]:
        """获取状态检查规则"""
        return self.config.get("status_checks", [])

    def get_error_handling(self) -> List[Dict[str, str]]:
        """获取错误处理规则"""
        return self.config.get("error_handling", [])

    def get_standalone_agents(self) -> List[Dict[str, Any]]:
        """获取独立 Agent 调用点"""
        return self.config.get("standalone_agents", [])

    def get_outputs(self) -> List[Dict[str, str]]:
        """获取输出位置"""
        return self.config.get("outputs", [])

    def validate(self) -> tuple[bool, List[str]]:
        """
        验证配置文件的完整性
        
        Returns:
            (是否有效, 错误信息列表)
        """
        errors = []
        
        # 检查必要字段
        if "workflow" not in self.config:
            errors.append("缺少 workflow 根节点")
        
        if "steps" not in self.config or len(self.config.get("steps", [])) == 0:
            errors.append("缺少 steps 定义或 steps 为空")
        
        # 检查每个步骤的必要字段
        for i, step in enumerate(self.get_steps()):
            if "id" not in step:
                errors.append(f"步骤 {i} 缺少 id 字段")
            if "name" not in step:
                errors.append(f"步骤 {i} 缺少 name 字段")
        
        return len(errors) == 0, errors

    def to_dict(self) -> Dict[str, Any]:
        """返回完整的配置字典"""
        return self.config