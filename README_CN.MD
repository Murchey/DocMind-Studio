# DocMind-Studio

> AI 驱动的多类型文档总结与输出平台

[English](./README.MD)

---

## 项目概述

DocMind-Studio 是一个 AI 驱动的多文档分析、结构化知识库构建和自动化输出平台。类似 Google NotebookLM，但具备多文件知识库总结和索引能力，能将零散文档转化为结构化、可操作的输出成果。

**核心理念**：将多种文档源（DOC、DOCX、PDF、PPT、Excel、TXT、MD）转化为结构化知识库和专业输出（报告、演示文稿、格式化文档）。

---

## 核心特性

- **多文档处理**：同时处理 DOC、DOCX、PDF、PPTX、XLSX、TXT、MD 文件
- **结构化知识库**：构建可搜索、可链接的知识仓库，含 JSON 索引
- **工作流引擎**：预置学术、企业、自定义场景的工作流
- **Agent 系统**：模块化 Agent 处理特定任务（文档分析、Excel 处理、PPT 生成）
- **增量更新**：支持迭代优化，无需从头开始
- **多格式输出**：生成 DOCX、PPTX、Excel、Markdown、HTML 等格式

---

## 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                    AGENTS.md (调度器)                         │
│         工作区初始化、Agent 调度、数据传递                      │
└─────────────────────────┬───────────────────────────────────┘
                          │
        ┌─────────────────┼─────────────────┐
        ▼                 ▼                 ▼
┌───────────────┐ ┌───────────────┐ ┌───────────────┐
│   工作流       │ │   工作流       │ │   工作流       │
│  知识库构建    │ │  学术文档处理  │ │  企业文档处理  │
└───────┬───────┘ └───────┬───────┘ └───────┬───────┘
        │                 │                 │
        ▼                 ▼                 ▼
┌─────────────────────────────────────────────────────────────┐
│                    ComponentAgents (Agent 集群)               │
│  doc-content │ doc-form │ excel │ ppt-deep │ ppt-master │ ...│
└─────────────────────────────────────────────────────────────┘
```

---

## Agent 列表

| Agent | 功能 | 输入格式 | 输出格式 |
|-------|------|----------|----------|
| `doc-content-analysis` | 文档内容提取与分析 | DOC/DOCX/PDF | JSON + MD |
| `doc-form-master` | 文档格式化与转换 | MD/DOCX | DOCX/PDF |
| `excel-master` | Excel 处理与分析 | XLSX/XLS/CSV | XLSX |
| `ppt-deep-summary` | PPT 内容总结 | PPTX | JSON + MD + HTML |
| `ppt-master` | PPT 生成 | PDF/DOCX/MD | PPTX |
| `ppt-continuation-tool` | PPT 续写 | PPTX + DOCX | PPTX |
| `phd-research-agent` | 论文辅助审阅 | DOCX | 建议文档 |

---

## 工作流

### KnowledgeBuilder（知识库构建）
将多个文档转化为结构化知识库，含索引、关键词和交叉引用。

**触发关键词**：知识库、结构化、批量处理、关键词提取

### AcademicDocs（学术文档处理）
处理学术论文，包括格式化、引用管理和论文准备。

**触发关键词**：论文、学术、文献、格式化

### EnterpriseDocs（企业文档处理）
分析企业文档，包括会议纪要、报告和数据表格。

**触发关键词**：报告、企业、会议纪要、数据分析

---

## 应用场景

### 学术/课程场景
- 接收学长半途交付的项目资料
- 生成完整的答辩 PPT 和项目申报书
- 整合零散不完整的结课资料
- 应对频繁修改需求，支持增量更新

**为什么需要 DocMind？**
- 自动梳理零散资料 → 抽取核心信息 → 生成成果文档
- 需求变更时支持增量更新
- 节省人工整理时间

**非它不可的时刻**：手上有 20+ 文档，明天要做出可展示的答辩成果。

### 企业/业务场景
- 整理多个项目表格、会议纪要和课程安排
- 对比和汇总多数据源
- 生成汇报表格、PPT 和计划文档

**为什么需要 DocMind？**
- Excel Master + Doc/PPT Master 自动生成对比和汇总
- Knowledge Builder 维护可成长的知识资产
- 避免重复人工操作

**非它不可的时刻**：手上有 10+ 表格和多份会议纪要，需要短时间内生成汇报成果。

---

## 项目价值

### 有了钉钉/企业微信/飞书，为什么还需要本项目？
企业级软件处理标准工作流很好，但缺乏深度定制能力。DocMind 擅长企业软件不优先处理的细粒度、个性化需求。

### 有了 Gemini/ChatGPT/千问/豆包，为什么还需要本项目？
这些 AI APP 是对话导向、单文件聚焦的工作方式。DocMind 构建可成长的多文件知识库，而非一次性输出。我们利用 AI 能力产出更好的结构化成果。

### 有 NotebookLM 和 AnythingLLM，为什么还需要本项目？
- **NotebookLM**：个人知识库能力强，但跨文件分析特定项目较弱
- **AnythingLLM**：通用型产品；DocMind 增加了工作流配置和 SKILL 扩展，更适配多场景
- **输出差异**：DocMind 输出可用的 DOCX 和 PPT 文件，而非大段文本

---

## 快速开始

### 1. 放置文档

```
WORKSPACE/{ProjectName}/
└── doc-content-analysis/
    └── input/
        ├── report1.docx
        ├── paper.pdf
        └── data.xlsx
```

### 2. 通过 AGENTS.md 运行

调度器（AGENTS.md）会：
1. 创建项目工作区
2. 初始化进度追踪
3. 调度到相应 Agent
4. 在 Agent 间传递数据
5. 收集最终输出

### 3. 获取输出

```
WORKSPACE/{ProjectName}/
├── doc-content-analysis/summary/   # 结构化分析
├── doc-form-master/output/         # 格式化文档
├── ppt-master/output/              # 生成的演示文稿
└── knowledge-base/                 # 知识库
```

---

## 工作区结构

```
DocMind-Studio/
├── AGENTS.md              # 调度器入口
├── ComponentAgents/       # Agent 实现（只读）
├── Workflows/             # 工作流配置
├── WORKSPACE/             # 项目工作区（按项目隔离）
└── DevelopDocs/           # 开发文档
```

---

## VS Code 插件

计划开发配套插件，支持：
- 快速预览生成的输出
- 工作流配置管理
- 进度监控
- 快速创建工作流

---

## 许可证

详见 [LICENSE](./LICENSE)。
