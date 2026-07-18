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
def execute_academic_docs(project_name: str, user_requirement: str, materials: list):
    """执行AcademicDocs工作流"""
    from pathlib import Path
    import subprocess
    
    ws = Path(f"WORKSPACE/{project_name}")
    
    # Step 1: 材料提取
    for mat in materials:
        subprocess.run([
            "python", "ComponentAgents/doc-content-analysis/SKILLS/doc-convertor/scripts/doc_converter.py",
            str(mat)
        ], check=True)
    
    # Step 2: 论文评审（根据需求类型）
    if "评审" in user_requirement or "修改" in user_requirement:
        subprocess.run([
            "python", "ComponentAgents/phd-research-agent/SKILLS/pre-submission-reviewer/scripts/reviewer.py",
            str(ws / "doc-content-analysis/summary/draft.md")
        ], check=True)
    
    # Step 3: 格式标准化
    subprocess.run([
        "python", "ComponentAgents/doc-form-master-main/SKILLS/markdown-converter/scripts/md_converter.py",
        str(ws / "phd-research-agent/summary/review_result.md")
    ], check=True)
    
    # Step 4: 知识库构建（可选）
    if len(materials) > 5:
        subprocess.run([
            "python", "ComponentAgents/doc-content-analysis/SKILLS/knowledge-builder/scripts/kb_manager.py",
            "update", "knowledge-base/", str(ws / "doc-content-analysis/summary/"), 
            str(ws / "doc-content-analysis/summary/manifest.json")
        ], check=True)
```

---

## 独立Agent调用点汇总

| 场景 | 独立调用Agent | 用途 |
|------|--------------|------|
| 提取单个材料 | `doc-content-analysis` | 内容提取 |
| 评估研究想法 | `phd-research-agent` + `idea-evaluator` | idea评分 |
| 论文审阅 | `phd-research-agent` + `pre-submission-reviewer` | 修改建议 |
| 起草Introduction | `phd-research-agent` + `intro-drafter` | 写作辅助 |
| 格式转换 | `doc-form-master` + `markdown-converter` | MD→DOCX |
| 格式标准化 | `doc-form-master` + `format-normalizer` | 排版优化 |
| 导出PDF | `doc-form-master` + `pdf-export` | 最终输出 |
| 构建知识库 | `KnowledgeBuilderWorkflow` | 增量更新 |

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
