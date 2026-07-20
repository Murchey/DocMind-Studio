﻿﻿﻿# 此文件用于调度所有的 AGENT

AGENTS 相当于 AGENT 能力的目录和工作方案的生成原则
AGENT 相当于 SKILL 的能力目录

## 工作流程

在 AGENTS.md，调用 WORKFLOW 中的工作流配置文件，根据用户需求，调度不同的 AGENT。

---

## 工作区规范

**所有 AGENT 的工作目录统一在根目录下 `WORKSPACE/` 中，按项目和 Agent 隔离。**

### 目录结构

```
DocMind-Studio/                        # 根目录
├── AGENTS.md                          # 调度器
├── ComponentAgents/                   # Agent 代码（只读，不存放工作数据）
│   ├── doc-content-analysis/
│   ├── doc-form-master-main/
│   ├── excel-master-main/
│   ├── ppt-deep-summary/
│   ├── phd-research-agent/
│   ├── ppt-master/
│   └── ppt-continuation-tool/
├── WORKSPACE/                         # 总工作区（根目录下）
│   └── {ProjectName}/                 # 项目工作区（PascalCase，由 AGENTS.md 创建）
│       ├── doc-content-analysis/      # Agent 工作目录
│       │   ├── input/
│       │   ├── converted/
│       │   └── summary/
│       ├── doc-form-master/           # Agent 工作目录
│       │   ├── input/
│       │   ├── output/
│       │   ├── parsed/
│       │   └── validated/
│       ├── excel-master/
│       ├── ppt-deep-summary/
│       ├── phd-research-agent/
│       ├── ppt-master/
│       └── ppt-continuation-tool/
```

### 命名规则

| 项目 | 规则 | 示例 |
|------|------|------|
| ProjectName | 用户文档/任务名称，PascalCase | `氯苯那敏论文` → `ChlorphenaminePaper` |
| AgentName | AGENTS.md 目录表中的短名 | `doc-form-master`、`doc-content-analysis` |

### 调度器职责（AGENTS.md）

1. **创建项目工作区**：`WORKSPACE/{ProjectName}/`
2. **复制用户文档**到对应 Agent 的 `input/` 子目录
3. **调用 AGENT**，传入工作区绝对路径
4. **清理**：任务完成后可选择保留或清理工作区

### AGENT 职责

1. **使用调度器传入的工作区路径**，不自行创建工作区
2. **SKILL 脚本路径**仍从 `ComponentAgents/{agent}/SKILLS/` 加载
3. **输出**写入工作区对应子目录

---

## AGENT 目录

| Agent | 路径 | 职责 |
|-------|------|------|
| doc-content-analysis | `ComponentAgents/doc-content-analysis/AGENT.md` | DOCX、PDF 文档内容读取与分析：批量转换、内容提取、图片提取、AI 总结 |
| doc-form-master | `ComponentAgents/doc-form-master-main/AGENT.md` | MD 文档转换 DOCX 文档，以及格式处理 |
| excel-master | `ComponentAgents/excel-master-main/AGENT.md` | Excel 表格处理与分析：多表格对比、数据图表生成、排课与日程安排 |
| ppt-deep-summary | `ComponentAgents/ppt-deep-summary/AGENT.md` | 可处理多 PPTX、PPT 文件的核心观点总结和内容梳理 |
| phd-research-agent | `ComponentAgents/phd-research-agent/AGENT.md` | 博导论文辅助 Agent，可对论文核心内容进行修改建议 |
| ppt-master | `ComponentAgents/ppt-master/AGENT.md` | 用于 PPT 生成的 Agent |
| ppt-continuation-tool | `ComponentAgents/ppt-continuation-tool/AGENT.md` | 接收外部半完成 PPTX 和相关 DOCX 资料，分析已完成内容，继续生成剩余页面并输出完整 PPTX |

---

## WORKFLOW 目录

| Workflow | 路径 | 说明 |
|----------|------|------|
| KnowledgeBuilder | `Workflows/KnowledgeBuilderWorkflow.md` | 文档 → 结构化知识库（JSON），支持增量更新 |
| AcademicDocs | `Workflows/AcdamicDocsWorkflow.md` | 学术文档处理：论文评审、格式更改、知识库构建 |
| EnterpriseDocs | `Workflows/EnterpriseDocsWorkflow.md` | 企业文档处理：会议纪要、表格对比、报告生成、PPT汇报 |
| Competition | `Workflows/CompetitionWorkflow.md` | 竞赛资源处理：资源解压、项目书解析、答辩PPT生成、知识库构建 |

---

## 调度规则

### 0. 工作区初始化（所有调度通用）

在调度任何 AGENT 之前，AGENTS.md 必须先创建项目工作区：

```python
import os, shutil
from pathlib import Path

# 1. 确定项目名称（从用户文档/任务推断，PascalCase）
project_name = "ChlorphenaminePaper"  # 例：氯苯那敏论文

# 2. 创建项目工作区
root = Path(__file__).parent  # DocMind-Studio 根目录
project_ws = root / "WORKSPACE" / project_name
project_ws.mkdir(parents=True, exist_ok=True)

# 3. 初始化进度追踪（必须）
import sys
sys.path.insert(0, str(root / 'ComponentAgents' / 'process-skill' / 'scripts'))
from progress_tracker import ProgressTracker
tracker = ProgressTracker(root=str(root / "WORKSPACE"))
task_id = tracker.create_task(
    project=project_name,
    workflow="KnowledgeBuilderWorkflow",
    agent="doc-content-analysis",
    steps=[
        {"id": "workspace-init", "name": "创建项目工作区"},
        {"id": "content-extraction", "name": "文档内容提取"},
        {"id": "knowledge-build", "name": "知识库构建"},
    ]
)

# 4. 更新进度 — 工作区创建完成
tracker.complete_step(task_id=task_id, step_id="workspace-init", message="工作区创建完成")

# 5. 为每个 AGENT 创建子工作区
agent_ws = project_ws / "doc-form-master"
(agent_ws / "input").mkdir(parents=True, exist_ok=True)
(agent_ws / "output").mkdir(parents=True, exist_ok=True)
# ... 其他 Agent 类似

# 4. 复制用户文档到 Agent 的 input/
shutil.copy("用户文档路径", agent_ws / "input" / "input.docx")
```

**ProjectName 命名**：从用户文档名或任务描述中提取，转为 PascalCase。如用户未指定，使用文档名。

### 1. 知识库构建（支持增量更新）

当用户需要将多个文档转换为结构化知识库时：

**首次构建**：
```
用户文档 → KnowledgeBuilderWorkflow
  Step 0: 创建 WORKSPACE/{ProjectName}/
  Step 1: doc-content-analysis（WORKSPACE/{ProjectName}/doc-content-analysis/）
      生成 manifest.json + summary.json（含 content_hash）
  Step 2: knowledge-builder（kb_manager.py init）
      全量构建 knowledge-base/
  输出：knowledge-base/（含 .kb_state.json）
```

**增量更新**（新增/修改/删除文档后）：
```
新文档 → doc-content-analysis（仅分析差异文档）
    ↓ 生成 manifest.json（含 content_hash）
    ↓
kb_manager.py update
    ↓ 对比 .kb_state.json 中的指纹
    ↓ +新增 / ~变更 / -删除 / =跳过
    ↓
增量合并索引（不重建整个知识库）
    ↓
knowledge-base/ 已更新（version += 1）
```

**状态查询**：
```bash
python ComponentAgents/doc-content-analysis/SKILLS/knowledge-builder/scripts/kb_manager.py status \
  knowledge-base/ \
  WORKSPACE/{ProjectName}/doc-content-analysis/summary/ \
  WORKSPACE/{ProjectName}/doc-content-analysis/summary/manifest.json
```

**触发关键词**：知识库、结构化、文档总结、批量处理、关键词提取、概念索引、增量更新

**调度代码示例**：
```python
import subprocess
from pathlib import Path

ws = Path(f"WORKSPACE/{project_name}/doc-content-analysis/summary/")
kb_dir = Path("knowledge-base/")
kb_script = Path("ComponentAgents/doc-content-analysis/SKILLS/knowledge-builder/scripts/kb_manager.py")

# 增量更新（自动检测 init 还是 update）
subprocess.run([
    "python", str(kb_script), "update",
    str(kb_dir), str(ws), str(ws / "manifest.json")
], check=True)
```

### 2. 文档格式处理

当用户需要转换文档格式时：

```
用户文档 → doc-form-master
  Step 0: 创建 WORKSPACE/{ProjectName}/doc-form-master/
  输出：WORKSPACE/{ProjectName}/doc-form-master/output/
```

### 3. 学术文档处理

当用户需要处理学术论文、文献时：

```
用户文档 → AcademicDocsWorkflow
  Step 0: 创建 WORKSPACE/{ProjectName}/
  输出：WORKSPACE/{ProjectName}/doc-form-master/output/
```

### 4. 企业文档处理

当用户需要处理企业报告、内部文档时：

```
用户文档 → EnterpriseDocsWorkflow
  Step 0: 创建 WORKSPACE/{ProjectName}/
  Step 1: doc-content-analysis（内容提取）
  Step 2: excel-master（表格对比 + 图表）
  Step 3: doc-form-master（研究报告）
  Step 4: ppt-master（汇报PPT）
  Step 5: KnowledgeBuilderWorkflow（知识库构建）
  输出：WORKSPACE/{ProjectName}/ppt-master/output/ + knowledge-base/
```

**触发关键词**：会议纪要、企业报告、表格对比、研究报告、汇报PPT、市场分析

**调度代码示例**：
```python
def execute_enterprise_docs(project_name: str, materials: list, tables: list):
    """执行EnterpriseDocs工作流"""
    from pathlib import Path
    import subprocess
    
    ws = Path(f"WORKSPACE/{project_name}")
    
    # Step 1: 内容提取
    for mat in materials:
        subprocess.run([
            "python", "ComponentAgents/doc-content-analysis/SKILLS/doc-convertor/scripts/doc_converter.py",
            str(mat)
        ], check=True)
    
    # Step 2: 表格对比
    for tbl in tables:
        subprocess.run([
            "python", "ComponentAgents/excel-master-main/skills/excel_chart/scripts/generate_chart.py",
            str(tbl)
        ], check=True)
    
    # Step 3-5: 报告、PPT、知识库...
```

### 5. 竞赛资源处理

当用户需要处理竞赛资源包时：

```
用户文档 → CompetitionWorkflow
  Step 0: 创建 WORKSPACE/{ProjectName}/
  Step 1: 解压 ZIP/7Z 资源包（外部处理）
  Step 2: doc-content-analysis（项目书/代码提取）
  Step 3: ppt-master（答辩PPT生成）
  Step 4: KnowledgeBuilderWorkflow（知识库构建）
  输出：WORKSPACE/{ProjectName}/ppt-master/output/ + knowledge-base/
```

**触发关键词**：竞赛、答辩、项目书、资源包、ZIP、7Z

**调度代码示例**：
```python
def execute_competition(project_name: str, zip_file: str):
    """执行CompetitionWorkflow"""
    from pathlib import Path
    import shutil, subprocess
    
    ws = Path(f"WORKSPACE/{project_name}")
    
    # Step 1: 解压（外部处理示例）
    # shutil.unpack_archive(zip_file, ws/"input/")
    
    # Step 2-4: 提取、PPT、知识库...
```

### 6. PPT 续写

当用户需要继续完成外部半完成的 PPT 时：

```
用户文档 → ppt-continuation-tool
  Step 0: 创建 WORKSPACE/{ProjectName}/ppt-continuation-tool/
  输入：外部半完成 .pptx + .docx 资料
  输出：WORKSPACE/{ProjectName}/ppt-continuation-tool/output/
  预览：http://localhost:5050（续写完成后可选启动）
```

**触发关键词**：继续完成 PPT、PPT 续写、补充 PPT、完成演示文稿、半完成 PPT

**调度代码示例**：
```python
def execute_ppt_continuation(project_name: str, pptx_file: str, docx_files: list):
    """执行 ppt-continuation-tool Agent"""
    workspace = Path(f"WORKSPACE/{project_name}/ppt-continuation-tool")
    workspace.mkdir(parents=True, exist_ok=True)
    
    # 创建输入目录
    input_dir = workspace / "input"
    input_dir.mkdir(exist_ok=True)
    
    # 复制输入文件
    shutil.copy(pptx_file, input_dir)
    for file in docx_files:
        shutil.copy(file, input_dir)
    
    # 读取 AGENT.md 作为执行配置
    agent_md = Path("ComponentAgents/ppt-continuation-tool/AGENT.md")
    # 按照 AGENT.md 中的流程执行
    # ...
    
    # 续写完成后，可选择启动预览服务器
    # 预览URL: http://localhost:5050
```

---

---

## Agent 间衔接规范

### 1. 状态检查机制

调度器通过检查 `manifest.json` 判断 Agent 执行状态：

```python
import json
from pathlib import Path

def check_agent_status(workspace_path: str) -> dict:
    """检查 Agent 执行状态"""
    manifest_path = Path(workspace_path) / "summary" / "manifest.json"
    
    if not manifest_path.exists():
        return {"status": "not_started"}
    
    with open(manifest_path, 'r', encoding='utf-8') as f:
        manifest = json.load(f)
    
    return {
        "status": manifest.get("status", "unknown"),
        "success_count": manifest.get("success_count", 0),
        "failed_count": manifest.get("failed_count", 0),
        "documents": manifest.get("documents", [])
    }
```

### 2. 数据传递流程

```
上游 Agent 完成
    
    
生成 manifest.json (status=completed)
    
    
调度器读取 manifest.json
    
    
复制 summary.md 到下游 Agent 的 input/
    
    
调用下游 Agent
```

**传递代码示例**：

```python
import shutil
import json

def pass_output_to_downstream(project_name: str, upstream_agent: str, downstream_agent: str):
    """将上游输出传递给下游 Agent"""
    upstream_summary = Path(f"WORKSPACE/{project_name}/{upstream_agent}/summary")
    downstream_input = Path(f"WORKSPACE/{project_name}/{downstream_agent}/input")
    downstream_input.mkdir(parents=True, exist_ok=True)
    
    manifest_path = upstream_summary / "manifest.json"
    with open(manifest_path, 'r', encoding='utf-8') as f:
        manifest = json.load(f)
    
    for doc in manifest.get("documents", []):
        if doc.get("status") == "success":
            summary_md = doc.get("summary_md")
            if summary_md and Path(summary_md).exists():
                dest = downstream_input / f"{Path(summary_md).stem}.md"
                shutil.copy(summary_md, dest)
```

### 3. 需求文档传递

当 doc-content-analysis 识别到需求文档时，调度器自动传递到目标 Agent：

```python
def pass_requirements(project_name: str):
    """传递需求文档到目标 Agent"""
    manifest_path = Path(f"WORKSPACE/{project_name}/doc-content-analysis/summary/manifest.json")
    
    with open(manifest_path, 'r', encoding='utf-8') as f:
        manifest = json.load(f)
    
    for doc in manifest.get("documents", []):
        if doc.get("document_type") == "requirement":
            target_agent = doc.get("target_agent")
            summary_md = doc.get("summary_md")
            
            if target_agent and summary_md:
                dest = Path(f"WORKSPACE/{project_name}/{target_agent}/input/需求.md")
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy(summary_md, dest)
```

### 4. 错误处理

| 场景 | 处理方式 |
|------|----------|
| manifest.json 不存在 | Agent 未执行，提示用户先执行上游 |
| status = "failed" | 读取 error 字段，决定跳过或终止 |
| status = "empty" | 无文件可处理，跳过下游 |
| status = "partial" | 部分成功，传递成功的文件 |

---

## ppt-master-main 整合说明

ppt-master-main 是独立的多角色协作系统，整合时需注意：

### 目录结构

```
ComponentAgents/ppt-master-main/
 AGENTS.md                  # 原始入口（保留）
 SKILLS/ppt-master/         # 主 Skill
    SKILL.MD              # 工作流定义
    scripts/              # 脚本
    templates/            # 模板
    workflows/            # 子工作流
    references/           # 参考文档
 requirements.txt
```

### 调度方式

调度 ppt-master 时，读取其 `SKILLS/ppt-master/SKILL.MD` 作为执行配置：

```python
def execute_ppt_master(project_name: str, input_files: list):
    """执行 ppt-master Agent"""
    workspace = Path(f"WORKSPACE/{project_name}/ppt-master")
    workspace.mkdir(parents=True, exist_ok=True)
    
    # 创建输入目录
    input_dir = workspace / "input"
    input_dir.mkdir(exist_ok=True)
    
    # 复制输入文件
    for file in input_files:
        shutil.copy(file, input_dir)
    
    # 读取 SKILL.MD 作为执行配置
    skill_md = Path("ComponentAgents/ppt-master-main/SKILLS/ppt-master/SKILL.MD")
    # 按照 SKILL.MD 中的流程执行
    # ...
```

### 输出处理

ppt-master 的输出在 `WORKSPACE/{ProjectName}/ppt-master/projects/<name>/exports/`，调度器将其复制到 `output/`：

```python
def collect_ppt_master_output(project_name: str):
    """收集 ppt-master 输出"""
    exports_dir = Path(f"WORKSPACE/{project_name}/ppt-master/projects/*/exports")
    output_dir = Path(f"WORKSPACE/{project_name}/ppt-master/output")
    output_dir.mkdir(exist_ok=True)
    
    for pptx in exports_dir.glob("*.pptx"):
        shutil.copy(pptx, output_dir)
```

---

## 使用方式

1. 用户描述需求
2. AGENTS.md 根据需求匹配 Workflow（参考 `Workflows/config/WorkflowIndex.yaml`）
3. **创建项目工作区** `WORKSPACE/{ProjectName}/` 及 Agent 子目录
4. **初始化进度追踪**（使用 ProgressTracker 或工作流执行器）
5. 复制用户文档到 Agent 的 `input/`
6. 调用 AGENT，传入工作区绝对路径
7. AGENT 加载 SKILL 执行具体任务
8. **检查 Agent 状态**（check_agent_status）
9. **传递输出到下游**（pass_output_to_downstream）
10. **任务完成时标记完成**（tracker.complete_task）

---

## 工作流执行器集成（新增）

AGENTS.md 可通过 `Workflows/executor/` 执行完整工作流：

```python
from Workflows.executor import WorkflowExecutor

def dispatch_workflow(user_requirement: str, project_name: str):
    """根据需求匹配并执行工作流"""
    root = Path(__file__).parent
    
    # 1. 匹配工作流配置
    workflow_config = None
    if any(kw in user_requirement for kw in ["知识库", "结构化", "增量更新"]):
        workflow_config = "Workflows/config/KnowledgeBuilderWorkflow.yaml"
    elif any(kw in user_requirement for kw in ["论文", "学术", "评审", "格式化"]):
        workflow_config = "Workflows/config/AcademicDocsWorkflow.yaml"
    elif any(kw in user_requirement for kw in ["会议纪要", "企业报告", "表格对比"]):
        workflow_config = "Workflows/config/EnterpriseDocsWorkflow.yaml"
    elif any(kw in user_requirement for kw in ["竞赛", "项目书", "资源包"]):
        workflow_config = "Workflows/config/CompetitionWorkflow.yaml"
    
    if not workflow_config:
        print("未匹配到工作流，使用传统调度方式")
        return
    
    # 2. 执行工作流
    executor = WorkflowExecutor(project_root=str(root))
    result = executor.execute(workflow_config, project_name)
    
    if result["success"]:
        print(f"工作流执行成功: {result['completed_steps']}")
    else:
        print(f"工作流执行失败: {result['error']}")
```

**工作流配置文件位置**：`Workflows/config/*.yaml`

**执行器状态文件**：`WORKSPACE/{ProjectName}/.workflow_state.json`（Dashboard 自动监听）

### 进度更新示例

```python
# 步骤开始
tracker.step_start(task_id=task_id, step_id="content-extraction", message="开始文档内容提取")

# 步骤进行中
tracker.step_progress(task_id=task_id, step_id="content-extraction", percent=50, message="正在处理文档1...")

# 步骤完成
tracker.complete_step(task_id=task_id, step_id="content-extraction", message="文档内容提取完成")

# 检查状态
status = check_agent_status(f"WORKSPACE/{project_name}/doc-content-analysis")
if status["status"] == "completed":
    # 传递到下游
    pass_output_to_downstream(project_name, "doc-content-analysis", "knowledge-builder")

# 任务完成
tracker.complete_task(task_id=task_id, message="所有任务完成")
```
