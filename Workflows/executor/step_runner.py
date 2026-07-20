"""
步骤执行器
Step Runner

负责执行单个工作流步骤，调用对应的 Agent
"""

import subprocess
from pathlib import Path
from typing import Dict, Any, Optional, Tuple


class StepRunner:
    """工作流步骤执行器"""

    def __init__(self, project_root: str = "."):
        """
        初始化步骤执行器
        
        Args:
            project_root: 项目根目录路径
        """
        self.project_root = Path(project_root).resolve()
        self.workspace_root = self.project_root / "WORKSPACE"

    def run_step(self, step: Dict[str, Any], project_name: str) -> Tuple[bool, str, Optional[Dict]]:
        """
        执行单个步骤
        
        Args:
            step: 步骤定义字典
            project_name: 项目名称
            
        Returns:
            (是否成功, 消息, 输出数据)
        """
        step_id = step.get("id", "unknown")
        step_name = step.get("name", "Unknown Step")
        step_type = step.get("type", "agent")
        
        print(f"[StepRunner] 执行步骤: {step_id} - {step_name}")
        
        # 根据步骤类型分发
        if step_type == "scheduler":
            return self._run_scheduler_step(step, project_name)
        elif step_type == "preprocessing":
            return self._run_preprocessing_step(step, project_name)
        else:
            return self._run_agent_step(step, project_name)

    def _run_scheduler_step(self, step: Dict[str, Any], project_name: str) -> Tuple[bool, str, Optional[Dict]]:
        """执行调度器步骤（工作区初始化等）"""
        step_name = step.get("name", "")
        
        if "初始化" in step_name:
            return self._init_workspace(project_name)
        
        return True, f"调度器步骤 {step_name} 跳过（无需执行）", None

    def _init_workspace(self, project_name: str) -> Tuple[bool, str, Optional[Dict]]:
        """初始化项目工作区"""
        from pathlib import Path as P
        
        ws = self.workspace_root / project_name
        ws.mkdir(parents=True, exist_ok=True)
        
        # 创建基础子目录（覆盖 AGENTS.md 中定义的全部 Agent）
        for agent_dir in [
            "doc-content-analysis",
            "doc-form-master",
            "excel-master",
            "ppt-deep-summary",
            "ppt-master",
            "ppt-continuation-tool",
            "phd-research-agent",
        ]:
            (ws / agent_dir / "input").mkdir(parents=True, exist_ok=True)
            (ws / agent_dir / "output").mkdir(parents=True, exist_ok=True)
        
        return True, f"工作区初始化完成: {ws}", {"workspace": str(ws)}

    def _run_preprocessing_step(self, step: Dict[str, Any], project_name: str) -> Tuple[bool, str, Optional[Dict]]:
        """执行预处理步骤（解压等）"""
        step_name = step.get("name", "")
        
        if "解压" in step_name:
            return True, "解压步骤由外部处理，跳过", None
        
        return True, f"预处理步骤 {step_name} 跳过", None

    def _run_agent_step(self, step: Dict[str, Any], project_name: str) -> Tuple[bool, str, Optional[Dict]]:
        """执行 Agent 调用步骤"""
        agent_name = step.get("agent", "")
        
        if not agent_name:
            return False, "步骤缺少 agent 字段", None
        
        # 获取 standalone_command（如果有）
        standalone = step.get("standalone_command", "")
        
        if standalone:
            # 执行独立命令
            return self._execute_command(standalone, project_name)
        
        # 否则尝试从 substeps 或其他字段推断
        substeps = step.get("substeps", [])
        if substeps:
            for substep in substeps:
                cmd = substep.get("command", "")
                if cmd:
                    success, msg, data = self._execute_command(cmd, project_name)
                    if not success:
                        return success, msg, data
        
        return True, f"Agent {agent_name} 步骤执行完成（模拟）", None

    def _execute_command(self, command: str, project_name: str) -> Tuple[bool, str, Optional[Dict]]:
        """
        执行 shell 命令
        
        Args:
            command: 命令字符串
            project_name: 项目名称（用于替换路径变量）
            
        Returns:
            (是否成功, 消息, 输出数据)
        """
        # 替换路径变量
        cmd = command.replace("{ProjectName}", project_name)
        cmd = cmd.replace("{project_name}", project_name)
        
        # 如果命令是 Python 脚本，添加项目根目录前缀
        if cmd.startswith("python "):
            # 已经是完整路径，保持不变
            pass
        elif cmd.startswith("python"):
            # 相对路径，添加项目根目录
            parts = cmd.split(" ", 1)
            if len(parts) == 2:
                script_path = self.project_root / parts[1].split()[0]
                cmd = f"python {script_path} {' '.join(parts[1].split()[1:])}"
        
        print(f"[StepRunner] 执行命令: {cmd}")
        
        try:
            result = subprocess.run(
                cmd,
                shell=True,
                cwd=str(self.project_root),
                capture_output=True,
                text=True,
                timeout=300  # 5分钟超时
            )
            
            if result.returncode == 0:
                return True, result.stdout or "命令执行成功", {"stdout": result.stdout}
            else:
                return False, f"命令执行失败: {result.stderr}", {"stderr": result.stderr}
                
        except subprocess.TimeoutExpired:
            return False, "命令执行超时", None
        except Exception as e:
            return False, f"命令执行异常: {str(e)}", None

    def check_agent_status(self, manifest_path: Path) -> str:
        """
        检查 Agent 执行状态
        
        Args:
            manifest_path: manifest.json 路径
            
        Returns:
            状态字符串: completed / failed / empty / partial / not_found
        """
        import json
        
        if not manifest_path.exists():
            return "not_found"
        
        try:
            with open(manifest_path, "r", encoding="utf-8") as f:
                manifest = json.load(f)
            
            return manifest.get("status", "unknown")
        except Exception:
            return "unknown"