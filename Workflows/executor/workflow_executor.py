"""
工作流主执行器
Workflow Executor

协调所有组件，按配置执行完整工作流
"""

from pathlib import Path
from typing import Dict, Any, Optional, Callable

from .yaml_parser import WorkflowParser
from .step_runner import StepRunner
from .state_manager import StateManager
from .error_handler import ErrorHandler, ErrorStrategy


class WorkflowExecutor:
    """工作流主执行器"""

    def __init__(
        self,
        project_root: str = ".",
        progress_callback: Optional[Callable] = None
    ):
        """
        初始化工作流执行器
        
        Args:
            project_root: 项目根目录
            progress_callback: 进度回调函数 (step_id, progress, message)
        """
        self.project_root = Path(project_root).resolve()
        self.progress_callback = progress_callback or (lambda *args: None)
        self.step_runner = StepRunner(str(self.project_root))
        self.parser: Optional[WorkflowParser] = None
        self.state_manager: Optional[StateManager] = None
        self.error_handler: Optional[ErrorHandler] = None

    def execute(
        self,
        workflow_config: str,
        project_name: str,
        user_inputs: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        执行工作流
        
        Args:
            workflow_config: 工作流 YAML 配置文件路径
            project_name: 项目名称
            user_inputs: 用户输入参数
            
        Returns:
            执行结果字典
        """
        print(f"[WorkflowExecutor] 开始执行工作流: {workflow_config}")
        print(f"[WorkflowExecutor] 项目: {project_name}")
        
        # 1. 解析配置
        self.parser = WorkflowParser(workflow_config)
        is_valid, errors = self.parser.validate()
        
        if not is_valid:
            return {
                "success": False,
                "error": "配置验证失败",
                "details": errors,
            }
        
        workflow_name = self.parser.get_workflow_name()
        print(f"[WorkflowExecutor] 工作流名称: {workflow_name}")
        
        # 2. 初始化状态管理器和错误处理器
        self.state_manager = StateManager(project_name)
        self.error_handler = ErrorHandler(self.parser.get_error_handling())
        
        # 3. 执行步骤
        steps = self.parser.get_steps()
        total_steps = len(steps)
        
        for i, step in enumerate(steps):
            step_id = step.get("id")
            step_name = step.get("name")
            
            progress = int((i / total_steps) * 100)
            self.progress_callback(step_id, progress, f"执行: {step_name}")
            
            # 检查条件
            if not self._check_step_condition(step):
                print(f"[WorkflowExecutor] 跳过步骤 {step_id}（条件不满足）")
                continue
            
            # 执行步骤
            self.state_manager.set_current_step(step_id)
            success, message, output = self.step_runner.run_step(step, project_name)
            
            if success:
                self.state_manager.mark_step_completed(step_id, output)
                print(f"[WorkflowExecutor] ✓ {step_id}: {message}")
            else:
                # 错误处理
                strategy = self.error_handler.handle_error(step_id, message)
                
                if strategy == ErrorStrategy.FAIL:
                    self.state_manager.mark_step_failed(step_id, message)
                    return {
                        "success": False,
                        "error": f"步骤 {step_id} 失败",
                        "message": message,
                        "completed_steps": self.state_manager.get_completed_steps(),
                    }
                elif strategy == ErrorStrategy.SKIP:
                    print(f"[WorkflowExecutor] 跳过步骤 {step_id}: {message}")
                    continue
        
        # 4. 完成
        self.progress_callback(None, 100, "工作流执行完成")
        
        return {
            "success": True,
            "workflow": workflow_name,
            "project": project_name,
            "completed_steps": self.state_manager.get_completed_steps(),
            "failed_steps": self.state_manager.get_failed_steps(),
        }

    def _check_step_condition(self, step: Dict[str, Any]) -> bool:
        """检查步骤执行条件"""
        condition = step.get("condition", "")
        
        if not condition:
            return True
        
        # 简单的条件检查逻辑
        if "用户要求构建知识库" in condition:
            # 这里可以扩展为更复杂的条件判断
            return True
        
        if "材料超过5份" in condition:
            return True
        
        return True

    def get_state(self) -> Optional[Dict[str, Any]]:
        """获取当前工作流状态"""
        if self.state_manager:
            return self.state_manager.to_dict()
        return None