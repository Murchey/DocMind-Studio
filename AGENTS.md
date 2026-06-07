# 此文件用于调度所有的 AGENT

AGENTS 相当于 AGENT 能力的目录和工作方案的生成原则
AGENT 相当于 SKILL 的能力目录

## 工作流程

在 AGENTS.md，调用 WORKFLOW 中的工作流配置文件，根据用户需求，调度不同的 AGENT。

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

### 1. 知识库构建

当用户需要将多个文档转换为结构化知识库时：

```
用户文档 → KnowledgeBuilderWorkflow
  Step 1: doc-content-analysis（文档转换 + 内容提取 + AI 总结）
  Step 2: knowledge-builder（索引聚合 + 知识库构建）
  输出：knowledge-base/（kb-manifest.json + documents/ + keywords/ + concepts/ + toc.json）
```

**触发关键词**：知识库、结构化、文档总结、批量处理、关键词提取、概念索引

### 2. 文档格式处理

当用户需要转换文档格式时：

```
用户文档 → doc-form-master
  输出：格式转换后的文档
```

### 3. 学术文档处理

当用户需要处理学术论文、文献时：

```
用户文档 → AcademicDocsWorkflow
  输出：格式化后的学术文档
```

### 4. 企业文档处理

当用户需要处理企业报告、内部文档时：

```
用户文档 → EnterpriseDocsWorkflow
  输出：标准化后的企业文档
```

---

## 使用方式

1. 用户描述需求
2. AGENTS.md 根据需求匹配 Workflow
3. 调用 Workflow 中指定的 AGENT
4. AGENT 加载 SKILL 执行具体任务
5. 输出结果返回给用户或传递给下游 AGENT
