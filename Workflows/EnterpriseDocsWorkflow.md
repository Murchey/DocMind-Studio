# 企业文档处理工作流

**目标**：处理企事业单位的文档内容，将复杂内容按照要求处理，并且构建知识库，将本次处理成果储存其中，输出要求文件。

---

## 工作流总览

```
会议纪要/报告/表格 → 需求分析
    ↓
Step 1: 内容提取（doc-content-analysis）
    ↓
Step 2: 表格数据对比（excel-master）
    ↓
Step 3: 研究报告生成（doc-form-master）
    ↓
Step 4: 汇报PPT生成（ppt-master）
    ↓
Step 5: 知识库构建（KnowledgeBuilderWorkflow）
    ↓
输出到工作区
```

---

## 经典场景

### 场景A：会议纪要整理

**输入**：会议纪要 + 重要性参考文档
**输出**：整理后的纪要 + 可成长式知识库

### 场景B：多表格对比分析

**输入**：10+表格 + 市场分析材料
**输出**：对比报告 + 可视化图表 + 知识库

### 场景C：汇报材料生成

**输入**：会议纪要 + 表格 + 分析结果
**输出**：研究报告 + 汇报PPT + 知识库

---

## 详细流程

### Step 0: 工作区初始化

调度器创建项目工作区：
```
WORKSPACE/{ProjectName}/
├── doc-content-analysis/
├── excel-master/
├── ppt-master/
└── knowledge-builder/
```

### Step 1: 内容提取

**调用**：`doc-content-analysis`
**输入**：用户上传的会议纪要、报告、参考文档
**输出**：`summary/manifest.json` + 各文档的 `summary.json`

**独立调用点**：
```bash
# 提取单个会议纪要
python ComponentAgents/doc-content-analysis/SKILLS/doc-convertor/scripts/doc_converter.py input.docx
```

### Step 2: 表格数据对比

**调用**：`excel-master`
**输入**：用户上传的Excel表格
**输出**：对比结果、图表、分析报告

**子步骤**：
1. **多表格智能对比**（`excel_compare`）
   - 对比多表格数据，识别差异和趋势
   
2. **可视化图表生成**（`excel_chart`）
   ```bash
   python ComponentAgents/excel-master-main/skills/excel_chart/scripts/generate_chart.py data.xlsx
   ```

3. **数据分析**（`excel_analysis`）
   ```bash
   python ComponentAgents/excel-master-main/skills/excel_analysis/scripts/analysis.py data.xlsx
   ```

**独立调用点**：
```bash
# 多表格对比
# 调用 excel_compare skill

# 生成可视化图表
python ComponentAgents/excel-master-main/skills/excel_chart/scripts/generate_chart.py data.xlsx

# 数据分析
python ComponentAgents/excel-master-main/skills/excel_analysis/scripts/analysis.py data.xlsx
```

### Step 3: 研究报告生成

**调用**：`doc-form-master`
**输入**：Step-1 + Step-2 的分析结果
**输出**：格式化研究报告（DOCX）

**子步骤**：
1. **报告内容整合**：汇总会议纪要 + 表格分析结果
2. **格式化输出**（`report-generator`）
   ```bash
   python ComponentAgents/doc-form-master-main/SKILLS/report-generator/scripts/generate_report.py
   ```

**独立调用点**：
```bash
# 生成研究报告
python ComponentAgents/doc-form-master-main/SKILLS/report-generator/scripts/generate_report.py
```

### Step 4: 汇报PPT生成

**调用**：`ppt-master`
**输入**：Step-3 的研究报告 + 关键数据
**输出**：汇报演示文稿（PPTX）

**说明**：调用 `ppt-master-main` 的 `SKILL.md` 流程，自动化生成结构化PPT

**独立调用点**：
```bash
# 调用 ppt-master 流程
python ComponentAgents/ppt-master-main/skills/ppt-master/SKILL.md
```

### Step 5: 知识库构建

**调用**：`KnowledgeBuilderWorkflow`
**输入**：所有处理后的材料
**输出**：可成长式知识库

**触发条件**：默认执行（企业文档通常需要长期积累）

---

## 调度代码示例

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
    
    # Step 3: 报告生成
    subprocess.run([
        "python", "ComponentAgents/doc-form-master-main/SKILLS/report-generator/scripts/generate_report.py"
    ], check=True)
    
    # Step 4: PPT生成
    # 调用 ppt-master 流程（通过 SKILL.md 执行）
    
    # Step 5: 知识库构建
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
| 提取会议纪要内容 | `doc-content-analysis` | 内容提取 |
| 多表格对比 | `excel-master` + `excel_compare` | 智能对比 |
| 生成可视化图表 | `excel-master` + `excel_chart` | 图表生成 |
| 数据分析 | `excel-master` + `excel_analysis` | 趋势分析 |
| 生成研究报告 | `doc-form-master` + `report-generator` | 报告输出 |
| 生成汇报PPT | `ppt-master` | PPT自动化生成 |
| 构建知识库 | `KnowledgeBuilderWorkflow` | 增量更新 |

---

## 输出位置

```
WORKSPACE/{ProjectName}/
├── doc-content-analysis/summary/    # 内容提取结果
├── excel-master/output/             # 表格对比、图表、分析结果
├── doc-form-master/output/          # 研究报告（DOCX）
├── ppt-master/output/               # 汇报PPT（PPTX）
└── knowledge-base/                  # 知识库
```

---

## 状态检查

| 步骤 | 检查条件 | 处理方式 |
|------|----------|----------|
| Step-1 | `manifest.json` 中 `status == "completed"` | 继续 Step-2 |
| Step-2 | 所有SKILL完成 | 继续 Step-3 |
| Step-3 | 报告生成完成 | 继续 Step-4 |
| Step-4 | PPT生成完成 | 继续 Step-5 |

---

## 错误处理

| 场景 | 处理方式 |
|------|----------|
| 表格格式不兼容 | 调用 `excel_compat` 转换后重试 |
| 内容提取失败 | 跳过该文档，继续处理其他 |
| PPT生成失败 | 降级为纯文本报告输出 |

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