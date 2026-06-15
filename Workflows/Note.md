# 工作流描述规范

> 本文档定义如何编写工作流配置文件，供开发人员和 AI 对接时参考。

---

## 1. 工作流文件结构

工作流配置文件存放在 `Workflows/` 目录下，使用 Markdown 格式，包含以下部分：

```markdown
# {工作流名称}

## 触发条件
描述何时调用此工作流（关键词、用户意图等）

## 步骤定义
按顺序列出工作流步骤

## 数据流
描述输入输出和 Agent 间数据传递
```

---

## 2. 步骤描述格式

每个步骤使用以下格式：

```markdown
### Step N: {步骤名称}

**Agent**: `{agent-name}`
**输入**: `{输入路径或来源}`
**输出**: `{输出路径}`
**条件**: {可选，执行条件}
**说明**: {补充说明}
```

---

## 3. 示例：单 Agent 工作流

```markdown
# 文档格式化工作流

## 触发条件
- 用户要求转换文档格式
- 关键词：格式化、排版、DOCX、学术论文

## 步骤定义

### Step 1: 文档格式化

**Agent**: `doc-form-master`
**输入**: `WORKSPACE/{ProjectName}/doc-form-master/input/`
**输出**: `WORKSPACE/{ProjectName}/doc-form-master/output/`
**说明**: 将 MD/DOCX 转换为格式化的学术文档

## 数据流

输入文件 → doc-form-master → 格式化后的 .docx
```

---

## 4. 示例：多 Agent 串联工作流

```markdown
# 知识库构建工作流

## 触发条件
- 用户需要将文档转为结构化知识库
- 关键词：知识库、结构化、批量处理

## 步骤定义

### Step 1: 文档内容提取

**Agent**: `doc-content-analysis`
**输入**: `WORKSPACE/{ProjectName}/doc-content-analysis/input/`
**输出**: `WORKSPACE/{ProjectName}/doc-content-analysis/summary/`
**关键输出**: `manifest.json`, `summary.json`

### Step 2: 知识库构建

**Agent**: `knowledge-builder`
**输入**: Step 1 的 `summary/manifest.json`
**输出**: `WORKSPACE/{ProjectName}/knowledge-base/`
**条件**: Step 1 的 `manifest.json` 中 `status == "completed"`

## 数据流

用户文档
    ↓
[doc-content-analysis]
    ↓ manifest.json + summary.json
[knowledge-builder]
    ↓
结构化知识库
```

---

## 5. 示例：条件分支工作流

```markdown
# 文档处理工作流

## 触发条件
- 用户上传文档进行处理

## 步骤定义

### Step 1: 文档分析

**Agent**: `doc-content-analysis`
**输入**: 用户文档
**输出**: `manifest.json` + `summary.json`

### Step 2a: 知识文档处理

**Agent**: `knowledge-builder`
**条件**: `summary.json` 中 `document_type == "knowledge"`
**输入**: Step 1 输出的 `summary.json`
**输出**: 知识库索引

### Step 2b: 需求文档处理

**Agent**: `{target_agent}`
**条件**: `summary.json` 中 `document_type == "requirement"`
**输入**: Step 1 输出的 `summary.md`
**输出**: 根据 `target_agent` 字段确定

## 数据流

文档 → [doc-content-analysis] → 检查 document_type
                                    ├─ knowledge → [knowledge-builder]
                                    └─ requirement → [target_agent]
```

---

## 6. 示例：带用户交互的工作流

```markdown
# 学术文档处理工作流

## 触发条件
- 用户需要格式化学术论文

## 步骤定义

### Step 1: 文档解析

**Agent**: `doc-form-master`
**输入**: `WORKSPACE/{ProjectName}/doc-form-master/input/`
**输出**: `WORKSPACE/{ProjectName}/doc-form-master/parsed/`

### Step 2: 用户确认（交互点）

**类型**: 用户交互
**方式**: 启动 Web 预览服务器
**操作**: 用户在浏览器中确认格式设计
**输出**: `workspace/validated/edited_config.json`

### Step 3: 格式化生成

**Agent**: `doc-form-master`
**输入**: 解析结果 + 用户确认配置
**输出**: `WORKSPACE/{ProjectName}/doc-form-master/output/`

## 数据流

文档 → [解析] → [用户确认] → [格式化] → 输出
```

---

## 7. 数据传递描述

### 7.1 直接传递

```markdown
**输入**: Step 1 输出的 `{workspace}/summary/manifest.json`
```

### 7.2 条件传递

```markdown
**输入**: 
- 若 `document_type == "knowledge"` → knowledge-builder
- 若 `document_type == "requirement"` → 根据 `target_agent` 字段选择
```

### 7.3 路径模板

| 变量 | 说明 | 示例 |
|------|------|------|
| `{ProjectName}` | 项目名称（PascalCase） | `ChlorphenaminePaper` |
| `{agent-name}` | Agent 短名 | `doc-content-analysis` |
| `{workspace}` | Agent 工作区路径 | `WORKSPACE/{ProjectName}/{agent-name}` |

---

## 8. 状态检查描述

在工作流中引用 Agent 状态时，使用以下格式：

```markdown
**条件**: `{workspace}/summary/manifest.json` 中 `status == "completed"`
```

状态值说明：

| 状态 | 含义 | 处理方式 |
|------|------|----------|
| `completed` | 全部成功 | 继续下一步 |
| `failed` | 失败 | 终止或跳过 |
| `empty` | 无输入 | 跳过 |
| `partial` | 部分成功 | 处理成功的部分 |

---

## 9. 完整工作流模板

```markdown
# {工作流名称}

## 概述
{一句话说明工作流用途}

## 触发条件
- {触发关键词或用户意图}

## 步骤定义

### Step 1: {步骤名称}

**Agent**: `{agent-name}`
**输入**: `{输入路径}`
**输出**: `{输出路径}`
**条件**: {可选}
**说明**: {可选}

### Step 2: {步骤名称}
...

## 数据流

{用 ASCII 图描述数据流向}

## 错误处理

| 场景 | 处理方式 |
|------|----------|
| {错误场景} | {处理方式} |
```

---

## 附录：现有工作流参考

| 工作流 | 文件 | 说明 |
|--------|------|------|
| KnowledgeBuilder | `Workflows/KnowledgeBuilderWorkflow.md` | 文档→知识库 |
| AcademicDocs | `Workflows/AcdemicDocsWorkflow.md` | 学术文档处理 |
| EnterpriseDocs | `Workflows/EnterpriseDocsWorkflow.md` | 企业文档处理 |
