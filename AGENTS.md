# 此文件用于调度所有的 AGENT

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
│   ├── ppt-master-main/
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
│       ├── ppt-continuation-tool/
│       └── 成果/                      # ⭐ 项目最终产出汇总（所有工作流完成后）
│           ├── README.md              # 成果清单说明
│           ├── *.docx                 # 最终文档
│           ├── *.pptx                 # 最终演示文稿
│           ├── *.xlsx                 # 最终表格
│           └── ...                    # 其他最终交付物
```

### 成果文件夹规范

所有工作流执行完毕后，调度器必须将**最终交付物**汇总到 `WORKSPACE/{ProjectName}/成果/` 目录：

- **汇总时机**：整个工作流所有 Step 均完成后，最后一步执行
- **汇总内容**：仅包含最终交付文件（DOCX/PPTX/XLSX/PDF 等），不含中间过程文件
- **README.md**：生成一份简要的成果清单说明，列出每个文件的用途和生成时间
- **目录结构**：扁平化存储，不嵌套 Agent 子目录

```python
def collect_final_outputs(project_name: str, output_summary: list):
    """
    收集所有最终交付物到成果文件夹
    
    Args:
        project_name: 项目名称
        output_summary: 最终文件清单，每项为 (源路径, 显示名称)
    """
    root = Path("d:/Projects/vibecoding/DocMind-Studio")
    output_dir = root / "WORKSPACE" / project_name / "成果"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    from datetime import datetime
    files = []
    
    for src_path, display_name in output_summary:
        src = Path(src_path)
        if src.exists():
            dest = output_dir / display_name
            shutil.copy2(str(src), str(dest))
            files.append({
                "file": display_name,
                "size": src.stat().st_size,
                "source": str(src.relative_to(root / "WORKSPACE" / project_name))
            })
    
    # 生成 README.md 成果清单
    readme = f"# {project_name} - 成果清单\n\n"
    readme += f"生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
    readme += "| 文件 | 大小 | 来源 |\n"
    readme += "|------|------|------|\n"
    for f in files:
        readme += f"| {f['file']} | {f['size']:,} B | {f['source']} |\n"
    
    (output_dir / "README.md").write_text(readme, encoding="utf-8")
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
| ppt-master | `ComponentAgents/ppt-master-main/AGENT.md` | 用于 PPT 生成的 Agent |
| ppt-continuation-tool | `ComponentAgents/ppt-continuation-tool/AGENT.md` | 接收外部半完成 PPTX 和相关 DOCX 资料，分析已完成内容，继续生成剩余页面并输出完整 PPTX |

---

## WORKFLOW 目录

| Workflow | 路径 | 说明 |
|----------|------|------|
| KnowledgeBuilder | `Workflows/KnowledgeBuilderWorkflow.md` | 文档 → 结构化知识库（JSON），支持增量更新 |
| AcademicDocs | `Workflows/AcdamicDocsWorkflow.md` | 学术文档处理：论文评审、格式更改、知识库构建 |
| EnterpriseDocs | `Workflows/EnterpriseDocsWorkflow.md` | 企业文档处理：会议纪要、表格对比、报告生成、PPT汇报 |
| Competition | `Workflows/CompetitionWorkflow.md` | 竞赛资源处理：3轮用户交互（类型/风格/赛道）→ 核心点提取 → 精简PPT + 知识库 |

---

## 调度规则

### ⚠️ 强制规范：进度同步（所有调度必须遵守）

**每个调度代码示例和实际执行中，必须在每个 Step 前后调用进度追踪器。** 这是插件 Dashboard 显示任务进度的唯一数据来源，跳过此步骤将导致用户在插件上看不到任何进度。

**最小进度同步模式**（每个 Step 必须包含）：

```python
# Step 开始
tracker.step_start(task_id=task_id, step_id="step-id", message="步骤名称开始")

# ... 执行 Step 内容 ...

# Step 完成
tracker.complete_step(task_id=task_id, step_id="step-id", message="步骤名称完成")
```

**完整进度同步模式**（长时间步骤建议使用）：

```python
# Step 开始
tracker.step_start(task_id=task_id, step_id="step-id", message="步骤名称开始")

# ... 执行中（可选进度更新） ...
tracker.step_progress(task_id=task_id, step_id="step-id", percent=50, message="处理中...")

# Step 完成
tracker.complete_step(task_id=task_id, step_id="step-id", message="步骤名称完成")
```

**所有调度代码示例中的 `subprocess.run()` 调用，都必须被 `tracker.step_start()` 和 `tracker.complete_step()` 包裹。**

---

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

### 1. 知识库构建（项目级，支持多 Agent 注册）

知识库是**项目级**资源，位于 `WORKSPACE/{ProjectName}/knowledge-base/`，任何 Agent 均可通过 `register` 命令将自己的摘要注册到项目知识库中。

**kb_manager.py CLI**：
```bash
# 首次构建（全量）
python kb_manager.py init {kb_dir} {summary_dir} {manifest} --agent {agent_name}

# 增量更新（对比 content_hash，+新增 / ~变更 / -删除 / =跳过）
python kb_manager.py update {kb_dir} {summary_dir} {manifest} --agent {agent_name}

# 跨 Agent 注册（其他 Agent 将摘要注册到已有知识库）
python kb_manager.py register {kb_dir} {agent_name} {manifest} [--summary-dir {dir}]

# 状态查询
python kb_manager.py status {kb_dir} [--summary-dir {dir}] [--manifest {path}]

# 知识查询（关键词/实体/文档/关系检索）
python kb_manager.py query {kb_dir} {keywords|entities|documents|relations} {text}
```

> `kb_dir` 在项目级场景下统一为 `WORKSPACE/{ProjectName}/knowledge-base/`。

**首次构建**：
```
用户文档 → KnowledgeBuilderWorkflow
  Step 0: 创建 WORKSPACE/{ProjectName}/
  Step 1: doc-content-analysis（WORKSPACE/{ProjectName}/doc-content-analysis/）
      生成 manifest.json + summary.json（含 content_hash）
  Step 2: kb_manager.py init（--agent doc-content-analysis）
      全量构建 WORKSPACE/{ProjectName}/knowledge-base/
  输出：WORKSPACE/{ProjectName}/knowledge-base/（含 .kb_state.json）
```

**增量更新**（新增/修改/删除文档后）：
```
新文档 → doc-content-analysis（仅分析差异文档）
    ↓ 生成 manifest.json（含 content_hash）
    ↓
kb_manager.py update --agent doc-content-analysis
    ↓ 对比 .kb_state.json 中的指纹
    ↓ +新增 / ~变更 / -删除 / =跳过
    ↓
增量合并索引（不重建整个知识库）
    ↓
WORKSPACE/{ProjectName}/knowledge-base/ 已更新（version += 1）
```

**跨 Agent 注册**（其他 Agent 将摘要汇入项目知识库）：
```
excel-master / ppt-master / doc-form-master 等 Agent 完成后
    ↓
kb_manager.py register {kb_dir} {agent_name} {manifest} --summary-dir {dir}
    ↓
项目知识库聚合多 Agent 成果
```

**状态查询**：
```bash
python ComponentAgents/doc-content-analysis/SKILLS/knowledge-builder/scripts/kb_manager.py status \
  WORKSPACE/{ProjectName}/knowledge-base/ \
  --summary-dir WORKSPACE/{ProjectName}/doc-content-analysis/summary/ \
  --manifest WORKSPACE/{ProjectName}/doc-content-analysis/summary/manifest.json
```

**触发关键词**：知识库、结构化、文档总结、批量处理、关键词提取、概念索引、增量更新

**调度代码示例**：
```python
import subprocess, sys
from pathlib import Path

project_name = "ExampleProject"
ws = Path(f"WORKSPACE/{project_name}")
summary_dir = ws / "doc-content-analysis" / "summary"
kb_dir = ws / "knowledge-base"
kb_script = Path("ComponentAgents/doc-content-analysis/SKILLS/knowledge-builder/scripts/kb_manager.py")

# 初始化进度追踪（强制）
root = Path("d:/Projects/vibecoding/DocMind-Studio")
sys.path.insert(0, str(root / 'ComponentAgents' / 'process-skill' / 'scripts'))
from progress_tracker import ProgressTracker
tracker = ProgressTracker(root=str(root / "WORKSPACE"))
task_id = tracker.create_task(
    project=project_name, workflow="KnowledgeBuilderWorkflow", agent="doc-content-analysis",
    steps=[
        {"id": "workspace-init", "name": "创建项目工作区"},
        {"id": "kb-init", "name": "知识库首次构建"},
        {"id": "kb-update", "name": "知识库增量更新"},
    ]
)
tracker.complete_step(task_id=task_id, step_id="workspace-init", message="工作区创建完成")

# 首次构建（含进度同步）
tracker.step_start(task_id=task_id, step_id="kb-init", message="开始知识库首次构建")
subprocess.run([
    "python", str(kb_script), "init",
    str(kb_dir), str(summary_dir), str(summary_dir / "manifest.json"),
    "--agent", "doc-content-analysis"
], check=True)
tracker.complete_step(task_id=task_id, step_id="kb-init", message="知识库首次构建完成")

# 增量更新（含进度同步）
tracker.step_start(task_id=task_id, step_id="kb-update", message="开始知识库增量更新")
subprocess.run([
    "python", str(kb_script), "update",
    str(kb_dir), str(summary_dir), str(summary_dir / "manifest.json"),
    "--agent", "doc-content-analysis"
], check=True)
tracker.complete_step(task_id=task_id, step_id="kb-update", message="知识库增量更新完成")

# 跨 Agent 注册（例如 excel-master 完成后）
excel_summary = ws / "excel-master" / "summary"
subprocess.run([
    "python", str(kb_script), "register",
    str(kb_dir), "excel-master", str(excel_summary / "manifest.json"),
    "--summary-dir", str(excel_summary)
], check=True)

# 任务完成
tracker.complete_task(task_id=task_id, message="知识库构建完成")
```

### 2. 文档格式处理

当用户需要转换文档格式时：

```
用户文档 → doc-form-master
  Step 0: 创建 WORKSPACE/{ProjectName}/doc-form-master/
  输出：WORKSPACE/{ProjectName}/doc-form-master/output/
```

### 3. 学术文档处理

当用户需要处理学术论文、文献、开题报告、论文评审时：

```
用户文档 → AcademicDocsWorkflow
  Step 0: 创建 WORKSPACE/{ProjectName}/ + 初始化进度追踪
  Step 1: doc-content-analysis（材料提取：PDF/DOCX → 内容提取 + AI 总结）
  Step 2: phd-research-agent（论文评审/idea评估/Introduction起草/开题报告生成）
  Step 3: doc-form-master（格式标准化：MD → 格式化 DOCX/PDF）
          ⭐ 自动集成：content_validator（乱码预检+后检）+ font_fixer（宋体强制）
  Step 4: 知识库构建（可选）
  输出汇总：WORKSPACE/{ProjectName}/成果/（最终交付物汇总）
  原始输出：WORKSPACE/{ProjectName}/doc-form-master/output/
```

**触发关键词**：论文、学术、评审、开题报告、文献综述、Introduction、idea评估、格式化论文

**phd-research-agent 调度说明**：
- 包含研究想法 → 调用 `idea-evaluator` SKILL
- 包含论文草稿需审阅 → 调用 `pre-submission-reviewer` SKILL
- 需要起草 Introduction → 调用 `intro-drafter` SKILL
- 需要生成开题报告/文献综述 → 调用 `pre-submission-reviewer` + AI 综合分析

**调度代码示例**：
```python
import shutil, subprocess, json
from pathlib import Path

# 0. 初始化（含进度追踪 —— 强制）
root = Path("d:/Projects/vibecoding/DocMind-Studio")
ws = root / "WORKSPACE" / project_name
ws.mkdir(parents=True, exist_ok=True)

import sys
sys.path.insert(0, str(root / 'ComponentAgents' / 'process-skill' / 'scripts'))
from progress_tracker import ProgressTracker
tracker = ProgressTracker(root=str(root / "WORKSPACE"))
task_id = tracker.create_task(
    project=project_name,
    workflow="AcademicDocsWorkflow",
    agent="doc-content-analysis",
    steps=[
        {"id": "workspace-init", "name": "创建项目工作区"},
        {"id": "material-extraction", "name": "材料内容提取"},
        {"id": "research-analysis", "name": "论文研究分析（phd-research-agent）"},
        {"id": "format-output", "name": "格式标准化输出"},
    ]
)
tracker.complete_step(task_id=task_id, step_id="workspace-init", message="工作区创建完成")

# 创建各 Agent 子目录
for agent in ["doc-content-analysis", "phd-research-agent", "doc-form-master"]:
    (ws / agent / "input").mkdir(parents=True, exist_ok=True)
    (ws / agent / "summary").mkdir(parents=True, exist_ok=True)
    (ws / agent / "output").mkdir(parents=True, exist_ok=True)

# 复制用户文档
for mat in materials:
    shutil.copy(str(mat), str(ws / "doc-content-analysis" / "input" / mat.name))

# Step 1: 材料提取（含进度同步）
tracker.step_start(task_id=task_id, step_id="material-extraction", message="开始材料内容提取")
subprocess.run([
    "python", "ComponentAgents/doc-content-analysis/SKILLS/doc-convertor/scripts/doc_converter.py",
    "process_all",
    str(ws / "doc-content-analysis" / "input"),
    str(ws / "doc-content-analysis")
], check=True)
tracker.complete_step(task_id=task_id, step_id="material-extraction", message="材料内容提取完成")

# Step 2: 论文研究分析 —— phd-research-agent（含进度同步）
tracker.step_start(task_id=task_id, step_id="research-analysis", message="开始论文研究分析")
# 将 doc-content-analysis 的 summary.md 传递到 phd-research-agent/input/
upstream_summary = ws / "doc-content-analysis" / "summary"
manifest_path = upstream_summary / "manifest.json"
if manifest_path.exists():
    with open(manifest_path, 'r', encoding='utf-8') as f:
        manifest = json.load(f)
    for doc in manifest.get("documents", []):
        if doc.get("status") == "success" and doc.get("summary_md"):
            src = Path(doc["summary_md"])
            if src.exists():
                shutil.copy(str(src), str(ws / "phd-research-agent" / "input" / src.name))

# 根据任务类型选择 phd-research-agent 的 SKILL
# （由调度器根据用户需求判断：idea评估 / 论文审阅 / Introduction起草 / 开题报告生成）
# 加载 ComponentAgents/phd-research-agent/AGENT.md 执行对应 SKILL
# 输出写入 ws / "phd-research-agent" / "summary/"
tracker.complete_step(task_id=task_id, step_id="research-analysis", message="论文研究分析完成")

# Step 3: 格式标准化（含进度同步）
tracker.step_start(task_id=task_id, step_id="format-output", message="开始格式标准化输出")
# 将 phd-research-agent 的输出复制到 doc-form-master/input/
phd_summary = ws / "phd-research-agent" / "summary"
for md_file in phd_summary.glob("*.md"):
    shutil.copy(str(md_file), str(ws / "doc-form-master" / "input" / md_file.name))
# ⭐ 内容校验：MD 预检（拦截乱码风险）
VALIDATOR = "ComponentAgents/doc-form-master-main/SKILLS/format-ai-checker/scripts/content_validator.py"
md_file = str(ws / "doc-form-master" / "input" / "*.md")
docx_file = str(ws / "doc-form-master" / "output" / "output.docx")

# 预检
import json
pre_check = subprocess.run(["python", VALIDATOR, "pre", md_file], capture_output=True, text=True)
if pre_check.returncode != 0:
    pre_report = json.loads(pre_check.stdout) if pre_check.stdout else {}
    tracker.complete_step(task_id=task_id, step_id="format-output",
        message="MD 预检未通过，请修复源文件中的乱码风险后再转换")
    print(f"[VALIDATOR] MD 预检未通过：{json.dumps(pre_report.get('issues', []), ensure_ascii=False, indent=2)}")
    tracker.complete_task(task_id=task_id, message="格式标准化中止：MD 内容校验未通过")
    return

# MD → DOCX
subprocess.run([
    "python", "ComponentAgents/doc-form-master-main/SKILLS/markitdown-converter/scripts/markitdown_converter.py",
    md_file, docx_file
], check=True)

# ⭐ 内容校验：DOCX 后检（验证输出无乱码）
post_check = subprocess.run(["python", VALIDATOR, "post", docx_file, md_file], capture_output=True, text=True)
if post_check.returncode != 0:
    post_report = json.loads(post_check.stdout) if post_check.stdout else {}
    print(f"[VALIDATOR] DOCX 后检发现问题：{json.dumps(post_report.get('issues', []), ensure_ascii=False, indent=2)}")
    print("[VALIDATOR] 输出文件可能存在乱码，建议修复 MD 源文件后重新转换")
tracker.complete_step(task_id=task_id, step_id="format-output", message="格式标准化输出完成（含内容校验）")

# 任务完成
tracker.complete_task(task_id=task_id, message="学术文档处理完成")
```

### 4. 企业文档处理

当用户需要处理企业报告、内部文档时：

```
用户文档 → EnterpriseDocsWorkflow
  Step 0: 创建 WORKSPACE/{ProjectName}/
  Step 1: doc-content-analysis（内容提取）
  Step 2: excel-master（表格对比 + 图表）
  Step 3: doc-form-master（研究报告 MD → DOCX）
  Step 3b: ⭐ content_validator（MD 预检 + DOCX 后检 — 拦截乱码风险）
  Step 4: ppt-master（汇报PPT）
  Step 5: kb_manager.py init --agent doc-content-analysis（项目知识库首次构建）
          各 Agent 完成后通过 register 汇入项目知识库
  输出汇总：WORKSPACE/{ProjectName}/成果/（最终交付物汇总）
  原始输出：WORKSPACE/{ProjectName}/ppt-master/output/ + WORKSPACE/{ProjectName}/knowledge-base/
```

**触发关键词**：会议纪要、企业报告、表格对比、研究报告、汇报PPT、市场分析

**调度代码示例**：
```python
import shutil, subprocess, json, sys
from pathlib import Path

def execute_enterprise_docs(project_name: str, materials: list, tables: list):
    """执行EnterpriseDocs工作流"""
    root = Path("d:/Projects/vibecoding/DocMind-Studio")
    ws = root / "WORKSPACE" / project_name
    kb_dir = ws / "knowledge-base"
    kb_script = root / "ComponentAgents/doc-content-analysis/SKILLS/knowledge-builder/scripts/kb_manager.py"

    # 初始化进度追踪（强制）
    sys.path.insert(0, str(root / 'ComponentAgents' / 'process-skill' / 'scripts'))
    from progress_tracker import ProgressTracker
    tracker = ProgressTracker(root=str(root / "WORKSPACE"))
    task_id = tracker.create_task(
        project=project_name, workflow="EnterpriseDocsWorkflow", agent="doc-content-analysis",
        steps=[
            {"id": "workspace-init", "name": "创建工作区"},
            {"id": "content-extraction", "name": "文档内容提取"},
            {"id": "excel-analysis", "name": "表格对比分析"},
            {"id": "report-generation", "name": "研究报告生成"},
            {"id": "ppt-generation", "name": "汇报PPT生成"},
            {"id": "knowledge-build", "name": "知识库构建"},
        ]
    )
    tracker.complete_step(task_id=task_id, step_id="workspace-init", message="工作区创建完成")

    # Step 1: 内容提取（含进度同步）
    tracker.step_start(task_id=task_id, step_id="content-extraction", message="开始文档内容提取")
    for mat in materials:
        subprocess.run([
            "python", str(root / "ComponentAgents/doc-content-analysis/SKILLS/doc-convertor/scripts/doc_converter.py"),
            str(mat)
        ], check=True)
    tracker.complete_step(task_id=task_id, step_id="content-extraction", message="文档内容提取完成")

    # Step 2: 表格对比（含进度同步）
    tracker.step_start(task_id=task_id, step_id="excel-analysis", message="开始表格对比分析")
    for tbl in tables:
        subprocess.run([
            "python", str(root / "ComponentAgents/excel-master-main/skills/excel_chart/scripts/generate_chart.py"),
            str(tbl)
        ], check=True)
    tracker.complete_step(task_id=task_id, step_id="excel-analysis", message="表格对比分析完成")

    # Step 3: 报告生成（含进度同步）
    tracker.step_start(task_id=task_id, step_id="report-generation", message="开始研究报告生成")
    # ... doc-form-master 生成研究报告（MD → DOCX）
    tracker.complete_step(task_id=task_id, step_id="report-generation", message="研究报告生成完成")

    # ⭐ Step 3b: 内容校验（MD 预检 + DOCX 后检 — 拦截乱码风险）
    VALIDATOR = root / "ComponentAgents/doc-form-master-main/SKILLS/format-ai-checker/scripts/content_validator.py"
    md_file = str(ws / "doc-form-master" / "input" / "*.md")
    docx_file = str(ws / "doc-form-master" / "output" / "*.docx")
    pre_check = subprocess.run(["python", str(VALIDATOR), "pre", md_file], capture_output=True, text=True)
    if pre_check.returncode != 0:
        pre_report = json.loads(pre_check.stdout) if pre_check.stdout else {}
        print(f"[VALIDATOR] MD 预检未通过，请修复后再转换: {json.dumps(pre_report.get('issues', []), ensure_ascii=False, indent=2)}")
    # MD → DOCX 转换已在上一步完成
    post_check = subprocess.run(["python", str(VALIDATOR), "post", docx_file, md_file], capture_output=True, text=True)
    if post_check.returncode != 0:
        print("[VALIDATOR] DOCX 后检发现问题，建议修复源 MD 后重新转换")

    # Step 4: PPT 生成（含进度同步）
    tracker.step_start(task_id=task_id, step_id="ppt-generation", message="开始汇报PPT生成")
    # ... ppt-master 生成汇报PPT
    tracker.complete_step(task_id=task_id, step_id="ppt-generation", message="汇报PPT生成完成")

    # Step 5: 知识库构建（含进度同步）
    tracker.step_start(task_id=task_id, step_id="knowledge-build", message="开始知识库构建")
    summary_dir = ws / "doc-content-analysis" / "summary"
    manifest = summary_dir / "manifest.json"
    if manifest.exists():
        subprocess.run([
            "python", str(kb_script), "init",
            str(kb_dir), str(summary_dir), str(manifest),
            "--agent", "doc-content-analysis"
        ], check=True)
    for agent_name in ["excel-master", "ppt-master"]:
        agent_manifest = ws / agent_name / "summary" / "manifest.json"
        if agent_manifest.exists():
            subprocess.run([
                "python", str(kb_script), "register",
                str(kb_dir), agent_name, str(agent_manifest),
                "--summary-dir", str(ws / agent_name / "summary")
            ], check=True)
    tracker.complete_step(task_id=task_id, step_id="knowledge-build", message="知识库构建完成")

    # 任务完成
    tracker.complete_task(task_id=task_id, message="企业文档处理完成")
```

### 5. 竞赛资源处理

当用户需要处理竞赛资源包时：

```
用户文档 → CompetitionWorkflow
  Step 0: 创建 WORKSPACE/{ProjectName}/
  Step 1: 解压 ZIP/7Z 资源包（外部处理）
  Step 2: doc-content-analysis（项目书/代码提取）
  Step 3a ⛔: PPT 类型选择（介绍型 / 答辩型）
  Step 3b ⛔: 视觉风格选择（学术风 / 科技风 / 简约风 / 商务风）
  Step 3c ⛔: 竞赛赛道选择（挑战杯 / 创青春 / 互联网+ / 通用）
  Step 3d: 策略矩阵匹配 → ppt_config.json
  核心点提取（每页 ≤ 5 条 × ≤ 15 字）
  Step 5: ppt-master（生成精简型 PPT）
  Step 6: kb_manager.py init --agent doc-content-analysis（项目知识库构建）
  输出汇总：WORKSPACE/{ProjectName}/成果/（最终交付物汇总）
  原始输出：WORKSPACE/{ProjectName}/ppt-master/output/ + WORKSPACE/{ProjectName}/knowledge-base/
```

**触发关键词**：竞赛、答辩、项目书、资源包、ZIP、7Z

**调度代码示例**：
```python
import shutil, subprocess, json, sys
from pathlib import Path

SUPPORTED_FORMATS = {".doc", ".docx", ".pdf", ".txt", ".md", ".pptx", ".xlsx"}

def execute_competition(project_name: str, zip_file: str = None, ppt_type: str = None):
    """执行CompetitionWorkflow"""
    root = Path("d:/Projects/vibecoding/DocMind-Studio")
    ws = root / "WORKSPACE" / project_name
    ws.mkdir(parents=True, exist_ok=True)

    # 初始化进度追踪（强制）
    sys.path.insert(0, str(root / 'ComponentAgents' / 'process-skill' / 'scripts'))
    from progress_tracker import ProgressTracker
    tracker = ProgressTracker(root=str(root / "WORKSPACE"))
    task_id = tracker.create_task(
        project=project_name, workflow="CompetitionWorkflow", agent="doc-content-analysis",
        steps=[
            {"id": "workspace-init", "name": "创建工作区"},
            {"id": "content-extraction", "name": "项目书内容提取"},
            {"id": "ppt-config", "name": "PPT策略配置"},
            {"id": "ppt-generation", "name": "PPT生成"},
            {"id": "knowledge-build", "name": "知识库构建"},
        ]
    )
    tracker.complete_step(task_id=task_id, step_id="workspace-init", message="工作区创建完成")

    # Step 0: 初始化子目录
    for agent in ["doc-content-analysis", "ppt-master"]:
        (ws / agent / "input").mkdir(parents=True, exist_ok=True)
        (ws / agent / "output").mkdir(parents=True, exist_ok=True)

    # Step 1: 解压或直接使用文档（含进度同步）
    tracker.step_start(task_id=task_id, step_id="content-extraction", name="开始项目书内容提取")
    if zip_file and Path(zip_file).exists():
        input_dir = ws / "input"
        input_dir.mkdir(exist_ok=True)
        shutil.unpack_archive(zip_file, input_dir)
        for f in input_dir.rglob("*"):
            if f.is_file() and f.suffix.lower() in SUPPORTED_FORMATS:
                shutil.copy2(f, ws / "doc-content-analysis" / "input" / f.name)

    # 检查输入是否为空
    if not list((ws / "doc-content-analysis" / "input").iterdir()):
        print("无可处理文档，工作流终止")
        tracker.complete_task(task_id=task_id, message="无可处理文档，工作流终止")
        return

    # Step 2: 内容提取
    # ... doc-convertor + AI 总结 → summary/ + manifest.json
    tracker.complete_step(task_id=task_id, step_id="content-extraction", message="项目书内容提取完成")

    # Step 3: PPT 类型选择 —— 用户交互（含进度同步）
    tracker.step_start(task_id=task_id, step_id="ppt-config", message="开始PPT策略配置")
    if ppt_type is None:
        ppt_type = "defense"  # 默认答辩型

    # 写入 ppt_type.json
    ppt_type_path = ws / "ppt-master" / "input" / "ppt_type.json"
    ppt_type_path.parent.mkdir(parents=True, exist_ok=True)
    with open(ppt_type_path, "w", encoding="utf-8") as f:
        json.dump({
            "type": ppt_type,
            "label": "介绍型 PPT" if ppt_type == "introduction" else "答辩型 PPT"
        }, f, ensure_ascii=False, indent=2)
    tracker.complete_step(task_id=task_id, step_id="ppt-config", message="PPT策略配置完成")

    # Step 4: PPT生成（含进度同步）
    tracker.step_start(task_id=task_id, step_id="ppt-generation", message="开始PPT生成")
    # 将 summary.md + ppt_type.json 复制到 ppt-master/input/
    # 加载 ppt-master-main/AGENT.md 执行生成流程（传入 ppt_type 控制风格）
    tracker.complete_step(task_id=task_id, step_id="ppt-generation", message="PPT生成完成")

    # Step 5: 知识库构建（含进度同步）
    tracker.step_start(task_id=task_id, step_id="knowledge-build", message="开始知识库构建")
    kb_dir = ws / "knowledge-base"
    kb_script = root / "ComponentAgents/doc-content-analysis/SKILLS/knowledge-builder/scripts/kb_manager.py"
    summary_dir = ws / "doc-content-analysis" / "summary"
    manifest = summary_dir / "manifest.json"
    if manifest.exists():
        with open(manifest, "r", encoding="utf-8") as f:
            data = json.load(f)
        if data.get("status") == "completed":
            subprocess.run([
                "python", str(kb_script), "init",
                str(kb_dir), str(summary_dir), str(manifest),
                "--agent", "doc-content-analysis"
            ], check=True)
    tracker.complete_step(task_id=task_id, step_id="knowledge-build", message="知识库构建完成")

    # 任务完成
    tracker.complete_task(task_id=task_id, message="竞赛资源处理完成")
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
import shutil, sys
from pathlib import Path

def execute_ppt_continuation(project_name: str, pptx_file: str, docx_files: list):
    """执行 ppt-continuation-tool Agent"""
    root = Path("d:/Projects/vibecoding/DocMind-Studio")
    workspace = root / "WORKSPACE" / project_name / "ppt-continuation-tool"
    workspace.mkdir(parents=True, exist_ok=True)

    # 初始化进度追踪（强制）
    sys.path.insert(0, str(root / 'ComponentAgents' / 'process-skill' / 'scripts'))
    from progress_tracker import ProgressTracker
    tracker = ProgressTracker(root=str(root / "WORKSPACE"))
    task_id = tracker.create_task(
        project=project_name, workflow="PptContinuation", agent="ppt-continuation-tool",
        steps=[
            {"id": "workspace-init", "name": "创建工作区"},
            {"id": "content-analysis", "name": "分析已完成内容"},
            {"id": "continuation", "name": "续写PPT"},
        ]
    )
    tracker.complete_step(task_id=task_id, step_id="workspace-init", message="工作区创建完成")

    # 创建输入目录
    input_dir = workspace / "input"
    input_dir.mkdir(exist_ok=True)

    # 复制输入文件
    shutil.copy(pptx_file, input_dir)
    for file in docx_files:
        shutil.copy(file, input_dir)

    # Step 1: 分析已完成内容（含进度同步）
    tracker.step_start(task_id=task_id, step_id="content-analysis", message="开始分析已完成内容")
    # 读取 AGENT.md 作为执行配置
    agent_md = root / "ComponentAgents/ppt-continuation-tool/AGENT.md"
    # 按照 AGENT.md 中的流程执行
    tracker.complete_step(task_id=task_id, step_id="content-analysis", message="已完成内容分析完成")

    # Step 2: 续写PPT（含进度同步）
    tracker.step_start(task_id=task_id, step_id="continuation", message="开始续写PPT")
    # ... 续写逻辑
    tracker.complete_step(task_id=task_id, step_id="continuation", message="PPT续写完成")

    # 任务完成
    tracker.complete_task(task_id=task_id, message="PPT续写完成")

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
    
    # 设置工作区环境变量（ppt-master 通过此变量定位项目路径）
    import os
    os.environ["DOCMIND_WORKSPACE"] = str(Path(f"WORKSPACE/{project_name}"))
    
    # 读取 SKILL.MD 作为执行配置
    skill_md = Path("ComponentAgents/ppt-master-main/SKILLS/ppt-master/SKILL.MD")
    # 按照 SKILL.MD 中的流程执行，project_manager.py init 会自动使用 WORKSPACE 路径
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
    elif any(kw in user_requirement for kw in ["竞赛", "答辩", "挑战杯", "创青春", "互联网+", "三创赛", "大创", "项目书", "资源包"]):
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
