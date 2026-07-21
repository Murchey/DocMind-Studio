# 学术文档处理工作流

**目标**：根据用户指令，帮助用户完成论文的评审、格式更改和数据分析补充。

---

## 工作流总览

```
用户需求 + 材料 → 需求分析
    ↓
Step 1: 材料提取（doc-content-analysis）
    ↓
Step 2: 论文评审（phd-research-agent）
    ↓
Step 3: 格式标准化（doc-form-master）
    ↓
Step 4: 知识库构建（KnowledgeBuilderWorkflow，可选）
    ↓
输出到工作区
```

---

## 经典场景

### 场景A：开题报告 → 论文大纲

**输入**：开题报告 + 相关论文材料 + 核心观点
**输出**：论文大纲 + 逐句解读 + 可成长式知识库

### 场景B：论文草稿 → 评审建议

**输入**：论文大纲 + 开题报告 + 论文idea
**输出**：idea评测 + 修改建议 + 调整后大纲

### 场景C：材料 → 格式化论文

**输入**：零散研究材料 + 用户格式要求
**输出**：格式化DOCX + PDF

---

## 详细流程

### Step 0: 工作区初始化

调度器创建项目工作区：
```
WORKSPACE/{ProjectName}/
├── doc-content-analysis/
├── phd-research-agent/
├── doc-form-master/
└── knowledge-builder/（可选）
```

### Step 1: 材料提取

**调用**：`doc-content-analysis`
**输入**：用户上传的开题报告、论文材料、参考文献
**输出**：`summary/manifest.json` + 各文档的 `summary.json`

**独立调用点**：
```bash
# 提取单个材料
python ComponentAgents/doc-content-analysis/SKILLS/doc-convertor/scripts/doc_converter.py input.docx
```

### Step 2: 论文评审

**调用**：`phd-research-agent`
**输入**：`doc-content-analysis` 输出的 `summary/*.md`
**输出**：评审报告或写作建议

**任务识别逻辑**：
- 包含研究想法 → `idea-evaluator`
- 包含论文草稿需审阅 → `pre-submission-reviewer`
- 需要起草Introduction → `intro-drafter`

**独立调用点**：
```bash
# 评估研究想法
python ComponentAgents/phd-research-agent/SKILLS/idea-evaluator/scripts/idea_evaluator.py idea.md

# 论文审阅
python ComponentAgents/phd-research-agent/SKILLS/pre-submission-reviewer/scripts/reviewer.py draft.md

# 起草Introduction
python ComponentAgents/phd-research-agent/SKILLS/intro-drafter/scripts/drafter.py research_info.md
```

### Step 3: 格式标准化

**调用**：`doc-form-master`
**输入**：评审后的内容或用户提供的MD草稿
**输出**：格式化DOCX + PDF

**格式化流程**：
1. MD → DOCX（markitdown-converter + pandoc）
2. 格式检测与标准化（format-normalizer）
3. 公式保护（formula-protection）
4. 页边距/字体调整（margin-manager、font-manager）
5. PDF导出（pdf-export）

**独立调用点**：
```bash
# MD转DOCX
python ComponentAgents/doc-form-master-main/SKILLS/markdown-converter/scripts/md_converter.py input.md

# 格式标准化
python ComponentAgents/doc-form-master-main/SKILLS/format-normalizer/scripts/normalizer.py input.docx

# 导出PDF
python ComponentAgents/doc-form-master-main/SKILLS/pdf-export/scripts/pdf_exporter.py input.docx
```

### Step 4: 知识库构建（可选）

**调用**：`KnowledgeBuilderWorkflow`
**输入**：所有处理后的材料
**输出**：可成长式知识库

**触发条件**：用户要求构建知识库或材料超过5份

---

## 调度代码示例

```python
import shutil, subprocess, json, sys
from pathlib import Path

def execute_academic_docs(project_name: str, user_requirement: str, materials: list):
    """执行AcademicDocs工作流"""
    root = Path("d:/Projects/vibecoding/DocMind-Studio")
    ws = root / "WORKSPACE" / project_name
    ws.mkdir(parents=True, exist_ok=True)

    # ⚠️ 进度追踪初始化（强制 —— 插件Dashboard数据来源）
    sys.path.insert(0, str(root / 'ComponentAgents' / 'process-skill' / 'scripts'))
    from progress_tracker import ProgressTracker
    tracker = ProgressTracker(root=str(root / "WORKSPACE"))
    task_id = tracker.create_task(
        project=project_name,
        workflow="AcademicDocsWorkflow",
        agent="doc-content-analysis",
        steps=[
            {"id": "workspace-init", "name": "创建工作区"},
            {"id": "material-extraction", "name": "材料内容提取"},
            {"id": "research-analysis", "name": "论文研究分析（phd-research-agent）"},
            {"id": "format-output", "name": "格式标准化输出"},
            {"id": "knowledge-build", "name": "知识库构建（可选）"},
        ]
    )
    tracker.complete_step(task_id=task_id, step_id="workspace-init", message="工作区创建完成")

    # 创建各 Agent 子目录
    for agent in ["doc-content-analysis", "phd-research-agent", "doc-form-master"]:
        (ws / agent / "input").mkdir(parents=True, exist_ok=True)
        (ws / agent / "summary").mkdir(parents=True, exist_ok=True)
        (ws / agent / "output").mkdir(parents=True, exist_ok=True)

    # 复制用户文档到 doc-content-analysis/input/
    for mat in materials:
        shutil.copy(str(mat), str(ws / "doc-content-analysis" / "input" / mat.name))

    # ==================== Step 1: 材料提取 ====================
    tracker.step_start(task_id=task_id, step_id="material-extraction", message="开始材料内容提取")
    for mat in materials:
        subprocess.run([
            "python", str(root / "ComponentAgents/doc-content-analysis/SKILLS/doc-convertor/scripts/doc_converter.py"),
            str(mat)
        ], check=True)
    tracker.complete_step(task_id=task_id, step_id="material-extraction", message="材料内容提取完成")

    # ==================== Step 2: phd-research-agent 论文研究分析 ====================
    tracker.step_start(task_id=task_id, step_id="research-analysis", message="开始论文研究分析")

    # 2a. 将 doc-content-analysis 的 summary/*.md 传递到 phd-research-agent/input/
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

    # 2b. 根据用户需求选择 phd-research-agent 的 SKILL（必须加载 Agent 的 AGENT.md 执行）
    #   - 研究想法 → idea-evaluator
    #   - 论文草稿审阅 → pre-submission-reviewer
    #   - Introduction 起草 → intro-drafter
    #   - 开题报告/文献综述 → pre-submission-reviewer + AI 综合分析
    # 加载 ComponentAgents/phd-research-agent/AGENT.md，按其执行流程处理
    # 输出写入 ws / "phd-research-agent" / "summary/"

    tracker.complete_step(task_id=task_id, step_id="research-analysis", message="论文研究分析完成")

    # ==================== Step 3: 格式标准化输出 ====================
    tracker.step_start(task_id=task_id, step_id="format-output", message="开始格式标准化输出")
    # 将 phd-research-agent 的输出复制到 doc-form-master/input/
    phd_summary = ws / "phd-research-agent" / "summary"
    for md_file in phd_summary.glob("*.md"):
        shutil.copy(str(md_file), str(ws / "doc-form-master" / "input" / md_file.name))
    # MD → DOCX（使用 markitdown-converter）
    # 格式标准化（使用 format-normalizer）
    # PDF导出（使用 pdf-export，可选）
    tracker.complete_step(task_id=task_id, step_id="format-output", message="格式标准化输出完成")

    # ==================== Step 4: 知识库构建（可选） ====================
    if len(materials) > 5:
        tracker.step_start(task_id=task_id, step_id="knowledge-build", message="开始知识库构建")
        subprocess.run([
            "python", str(root / "ComponentAgents/doc-content-analysis/SKILLS/knowledge-builder/scripts/kb_manager.py"),
            "update", "knowledge-base/", str(ws / "doc-content-analysis/summary/"),
            str(ws / "doc-content-analysis/summary/manifest.json")
        ], check=True)
        tracker.complete_step(task_id=task_id, step_id="knowledge-build", message="知识库构建完成")

    # 任务完成
    tracker.complete_task(task_id=task_id, message="学术文档处理完成")
```

---

## 独立Agent调用点汇总

| 场景 | 独立调用Agent | SKILL | 用途 |
|------|--------------|-------|------|
| 提取单个材料 | `doc-content-analysis` | doc-convertor | 内容提取 |
| 评估研究想法 | `phd-research-agent` | idea-evaluator | idea评分 |
| 论文审阅 | `phd-research-agent` | pre-submission-reviewer | 修改建议 |
| 起草Introduction | `phd-research-agent` | intro-drafter | 写作辅助 |
| 生成开题报告/文献综述 | `phd-research-agent` | pre-submission-reviewer + AI综合分析 | 开题报告/文献综述生成 |
| 格式转换 | `doc-form-master` | markitdown-converter | MD→DOCX |
| 格式标准化 | `doc-form-master` | format-normalizer | 排版优化 |
| 导出PDF | `doc-form-master` | pdf-export | 最终输出 |
| 构建知识库 | `KnowledgeBuilderWorkflow` | kb_manager.py | 增量更新 |

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

## 输出位置

```
WORKSPACE/{ProjectName}/
├── doc-content-analysis/summary/    # 材料提取结果
├── phd-research-agent/summary/      # 评审/写作建议
├── doc-form-master/output/          # 格式化DOCX/PDF
└── knowledge-base/                  # 知识库（可选）
```
