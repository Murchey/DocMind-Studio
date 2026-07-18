"""
错误处理器
Error Handler

负责工作流执行中的错误捕获、记录和恢复策略
"""

from typing import Dict, Any, Optional, Callable
from enum import Enum


class ErrorStrategy(Enum):
    """错误处理策略"""
    FAIL = "fail"           # 失败并终止
    SKIP = "skip"           # 跳过继续
    RETRY = "retry"         # 重试
    FALLBACK = "fallback"   # 降级处理


class ErrorHandler:
    """工作流错误处理器"""

    def __init__(self, error_rules: Optional[list] = None):
        """
        初始化错误处理器
        
        Args:
            error_rules: 错误处理规则列表
        """
        self.error_rules = error_rules or []
        self.error_log: list = []

    def handle_error(
        self,
        step_id: str,
        error: str,
        context: Optional[Dict] = None
    ) -> ErrorStrategy:
        """
        处理错误
        
        Args:
            step_id: 出错的步骤 ID
            error: 错误信息
            context: 上下文信息
            
        Returns:
            错误处理策略
        """
        # 记录错误
        self._log_error(step_id, error, context)
        
        # 查找匹配的规则
        for rule in self.error_rules:
            if self._match_rule(rule, step_id, error):
                strategy = ErrorStrategy(rule.get("action", "fail"))
                return strategy
        
        # 默认策略：失败
        return ErrorStrategy.FAIL

    def _match_rule(self, rule: Dict, step_id: str, error: str) -> bool:
        """检查规则是否匹配当前错误"""
        # 匹配步骤
        if "step" in rule and rule["step"] != step_id:
            return False
        
        # 匹配错误场景
        if "scenario" in rule:
            scenario = rule["scenario"]
            if scenario not in error:
                return False
        
        return True

    def _log_error(self, step_id: str, error: str, context: Optional[Dict]):
        """记录错误到日志"""
        entry = {
            "step_id": step_id,
            "error": error,
            "context": context or {},
            "timestamp": __import__("datetime").datetime.now().isoformat(),
        }
        self.error_log.append(entry)

    def get_error_log(self) -> list:
        """获取错误日志"""
        return self.error_log.copy()

    def clear_log(self):
        """清空错误日志"""
        self.error_log.clear()

    @staticmethod
    def get_default_rules() -> list:
        """获取默认错误处理规则"""
        return [
            {
                "scenario": "manifest 状态不是 completed",
                "action": "fail",
            },
            {
                "scenario": "无差异时执行 update",
                "action": "skip",
            },
            {
                "scenario": "输入文件不存在",
                "action": "skip",
            },
        ]