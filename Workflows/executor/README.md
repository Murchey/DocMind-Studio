# 工作流执行引擎

DocMind-Studio 工作流执行引擎，负责解析 YAML 配置并按步骤调用 Agent 完成复杂任务。

## 目录结构

```
Workflows/executor/
├── __init__.py              # 模块入口
├── yaml_parser.py           # YAML 配置解析器
├── step_runner.py           # 步骤执行器
├── state_manager.py         # 状态管理器
├── error_handler.py         # 错误处理器
├── workflow_executor.py     # 主执行器
└── README.md                # 本文档
```

## 核心组件

### 1. WorkflowParser (yaml_parser.py)
- 加载并解析 YAML 工作流配置文件
- 提供工作流元信息、步骤、触发条件、状态检查等访问接口
- 验证配置完整性

### 2. StepRunner (step_runner.py)
- 执行单个工作流步骤
- 支持调度器步骤、预处理步骤、Agent 调用步骤
- 执行 shell 命令并捕获输出
- 检查 Agent 状态（通过 manifest.json）

### 3. StateManager (state_manager.py)
- 跟踪工作流执行状态
- 记录已完成/失败步骤
- 保存步骤输出到 `.workflow_state.json`

### 4. ErrorHandler (error_handler.py)
- 捕获和记录错误
- 根据规则决定错误处理策略（fail/skip/retry/fallback）
- 提供默认错误规则

### 5. WorkflowExecutor (workflow_executor.py)
- 协调所有组件执行完整工作流
- 按顺序执行步骤、检查条件、处理错误
- 支持进度回调

## 使用示例

```python
from Workflows.executor import WorkflowExecutor

# 创建执行器
executor = WorkflowExecutor(project_root=".")

# 执行工作流
result = executor.execute(
    workflow_config="Workflows/config/KnowledgeBuilderWorkflow.yaml",
    project_name="ChlorphenaminePaper"
)

if result["success"]:
    print(f"工作流执行成功: {result['completed_steps']}")
else:
    print(f"工作流执行失败: {result['error']}")
```

## 执行流程

```
加载 YAML 配置
    ↓
验证配置
    ↓
初始化状态管理器
    ↓
遍历步骤:
    ├─ 检查条件
    ├─ 执行步骤 (StepRunner)
    ├─ 更新状态 (StateManager)
    └─ 错误处理 (ErrorHandler)
    ↓
返回执行结果
```

## 状态文件

执行过程中在 `WORKSPACE/{ProjectName}/.workflow_state.json` 保存状态：

```json
{
  "project_name": "ChlorphenaminePaper",
  "created_at": "2026-07-18T...",
  "updated_at": "2026-07-18T...",
  "current_step": "step-1",
  "completed_steps": ["step-0"],
  "failed_steps": [],
  "step_outputs": {}
}
```

## 扩展

- 添加新的步骤类型：在 `StepRunner._run_*_step` 方法中扩展
- 自定义错误规则：通过 `ErrorHandler` 传入规则列表
- 进度回调：通过 `progress_callback` 参数接收实时进度

---

## 脚本编码规范

> 工作流所有涉及中文内容的 Python 脚本，**必须直接书写中文字符**，禁止使用 Unicode 转义序列（如 `\u552F`）
> 
> ### 正确写法
> 
> ```python
> # ✅ 正确：直接写中文
> title = '哲学的唯物主义性'
> ```
> 
> ### 错误写法
> 
> ```python
> # ❌ 禁止：手写 Unicode 转义
> title = '\u54f2\u5b66\u7684\u5510\u7269\u4e3b\u4e49\u6027'
> ```
> 
> ### 原因
> - Python 3 原生支持 UTF-8，直接写中文无任何问题
> - Unicode 转义序列易写错（如 `\u552F` 错写为 `\u5510`）
> - 直接中文更易阅读和维护