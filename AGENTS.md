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
│   └── ppt-deep-summary-main/
├── WORKSPACE/                         # 总工作区（根目录下）
│   └── {ProjectName}/                 # 项目工作区（PascalCase，由 AGENTS.md 创建）
│       ├── doc-content-analysis/      # Agent 工作目录
│       │   ├── input/
│       │   ├── output/
│       │   └── summary/
│       ├── doc-form-master/           # Agent 工作目录
│       │   ├── input/
│       │   ├── output/
│       │   ├── parsed/
│       │   └── validated/
│       ├── excel-master/
│       └── ppt-deep-summary/
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
| doc-content-analysis | `ComponentAgents/doc-content-analysis/AGENT.md` | 文档内容读取与分析：批量转换、内容提取、图片提取、AI 总结 |
| doc-form-master | `ComponentAgents/doc-form-master-main/AGENT.md` | 文档格式转换与处理 |
| excel-master | `ComponentAgents/excel-master-main/AGENT.md` | Excel 文件处理 |
| ppt-deep-summary | `ComponentAgents/ppt-deep-summary-main/AGENT.md` | PPT 深度总结 |

---

## WORKFLOW 目录

| Workflow | 路径 | 说明 |
|----------|------|------|
| KnowledgeBuilder | `Workflows/KnowledgeBuilderWorkflow.md` | 文档 → 结构化知识库（JSON） |
| AcademicDocs | `Workflows/AcdamicDocsWorkflow.md` | 学术文档处理 |
| EnterpriseDocs | `Workflows/EnterpriseDocsWorkflow.md` | 企业文档处理 |

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

# 3. 为每个 AGENT 创建子工作区
agent_ws = project_ws / "doc-form-master"
(agent_ws / "input").mkdir(parents=True, exist_ok=True)
(agent_ws / "output").mkdir(parents=True, exist_ok=True)
# ... 其他 Agent 类似

# 4. 复制用户文档到 Agent 的 input/
shutil.copy("用户文档路径", agent_ws / "input" / "input.docx")
```

**ProjectName 命名**：从用户文档名或任务描述中提取，转为 PascalCase。如用户未指定，使用文档名。

### 1. 知识库构建

当用户需要将多个文档转换为结构化知识库时：

```
用户文档 → KnowledgeBuilderWorkflow
  Step 0: 创建 WORKSPACE/{ProjectName}/
  Step 1: doc-content-analysis（WORKSPACE/{ProjectName}/doc-content-analysis/）
  Step 2: knowledge-builder（WORKSPACE/{ProjectName}/knowledge-builder/）
  输出：WORKSPACE/{ProjectName}/knowledge-base/
```

**触发关键词**：知识库、结构化、文档总结、批量处理、关键词提取、概念索引

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
  输出：WORKSPACE/{ProjectName}/doc-form-master/output/
```

---

## 使用方式

1. 用户描述需求
2. AGENTS.md 根据需求匹配 Workflow
3. **创建项目工作区** `WORKSPACE/{ProjectName}/` 及 Agent 子目录
4. 复制用户文档到 Agent 的 `input/`
5. 调用 AGENT，传入工作区路径
6. AGENT 加载 SKILL 执行具体任务
7. 输出结果写入工作区，返回给用户或传递给下游 AGENT
