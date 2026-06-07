# DocMind 进度通知 JSON 对接规范

本文档用于约定 AGENTS 工程与 VS Code 插件之间的实时进度通知接口。AGENTS 调度器或具体 Agent 在执行任务时持续写入一个 JSON 文件，插件自动检测该文件并在 Dashboard 中展示任务进度。

## 1. 默认文件位置

插件默认读取：

```text
WORKSPACE/.docmind-progress.json
```

也会兼容以下常见路径：

```text
WORKSPACE/progress.json
.docmind/progress.json
docmind-progress.json
```

如果需要自定义路径，可在 VS Code 设置中配置：

```json
{
  "docmind.progressFile": "WORKSPACE/MyProject/progress.json"
}
```

路径建议相对于 DocMind-Studio 根目录书写。插件会监听配置路径，以及文件名包含 `progress` 的 JSON 文件变化。

## 2. 写入原则

AGENTS 端应把进度 JSON 当作“当前任务状态快照”，每次更新写完整内容，而不是只写增量。

建议使用原子写入，避免插件读取到半截 JSON：

1. 先写入临时文件，例如 `.docmind-progress.json.tmp`
2. 写完后替换为 `.docmind-progress.json`
3. 每个阶段开始、进度变化、产物生成、失败或完成时都更新一次

## 3. 推荐 Schema

```json
{
  "version": "1.0",
  "project": "ChlorphenaminePaper",
  "workflow": "KnowledgeBuilderWorkflow",
  "agent": "doc-content-analysis",
  "status": "running",
  "phase": "extracting",
  "message": "正在提取文档正文与图片",
  "progress": 42,
  "started_at": "2026-06-07T20:40:00+08:00",
  "updated_at": "2026-06-07T20:42:12+08:00",
  "current_step": "content-extraction",
  "steps": [
    {
      "id": "workspace-init",
      "name": "创建项目工作区",
      "agent": "AGENTS.md",
      "status": "completed",
      "progress": 100,
      "message": "WORKSPACE/ChlorphenaminePaper 已创建"
    },
    {
      "id": "content-extraction",
      "name": "文档内容提取",
      "agent": "doc-content-analysis",
      "status": "running",
      "progress": 55,
      "message": "正在处理 氯苯那敏论文.docx"
    },
    {
      "id": "knowledge-build",
      "name": "知识库构建",
      "agent": "knowledge-builder",
      "status": "pending",
      "progress": 0
    }
  ],
  "outputs": [
    {
      "label": "内容摘要",
      "path": "WORKSPACE/ChlorphenaminePaper/doc-content-analysis/summary/综合总结.json",
      "kind": "json"
    }
  ]
}
```

## 4. 字段说明

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `version` | string | 否 | 接口版本，建议从 `1.0` 开始 |
| `project` | string | 否 | 当前项目名，对应 `WORKSPACE/{ProjectName}` |
| `workflow` | string | 否 | 当前工作流名称 |
| `agent` | string | 否 | 当前正在执行的 Agent |
| `status` | string | 是 | 任务状态 |
| `phase` | string | 否 | 当前阶段，例如 `extracting`、`building` |
| `message` | string | 否 | 面向用户的简短状态说明 |
| `progress` | number | 否 | 总进度，范围 `0-100` |
| `started_at` | string | 否 | ISO 8601 开始时间 |
| `updated_at` | string | 否 | ISO 8601 更新时间 |
| `current_step` | string | 否 | 当前步骤 id 或名称 |
| `steps` | array | 否 | 步骤列表 |
| `outputs` | array | 否 | 当前已生成的产物 |
| `error` | string | 否 | 失败原因或异常摘要 |

## 5. 状态值约定

推荐使用以下状态值：

```text
idle
pending
running
completed
failed
cancelled
```

插件也兼容部分常见别名：

| 别名 | 归类 |
|------|------|
| `processing`、`in_progress`、`active` | running |
| `success`、`done`、`ready` | completed |
| `error` | failed |

## 6. 兼容字段

为了方便早期 AGENTS 工程快速接入，插件也兼容以下字段：

| 推荐字段 | 兼容字段 |
|----------|----------|
| `progress` | `percent` |
| `current_step` | `currentStep` |
| `started_at` | `startedAt` |
| `updated_at` | `updatedAt` |
| `steps` | `stages`、`tasks` |
| `outputs` | `artifacts`、`files` |
| `current_task` | `currentTask` |

如果存在 `current_task`，插件会优先从该对象读取 `workflow`、`agent`、`status`、`phase`、`message`、`progress` 等当前状态字段。

## 7. 产物与知识库文件

未来知识库可以由真实文件组成，例如：

```text
knowledge-base/
├── 氯苯那敏论文.docx
├── 图表数据.xlsx
├── 研究汇报.pptx
└── 原始材料.pdf
```

插件会在知识库中扫描并展示以下文件类型：

```text
.doc .docx .pdf .ppt .pptx .xls .xlsx .csv
```

用户点击这些文件时，插件会调用系统默认应用打开。Windows 上如果 `.docx`、`.pptx`、`.xlsx` 已关联到 Microsoft Office 或 WPS，就会直接用对应软件打开。

## 8. kb-manifest.json 中的文件路径

如果知识库有 `kb-manifest.json`，推荐在 `documents` 数组中写入真实文件路径：

```json
{
  "documents": [
    {
      "id": "doc_001",
      "title": "氯苯那敏论文",
      "source_file": "氯苯那敏论文.docx",
      "path": "WORKSPACE/ChlorphenaminePaper/knowledge-base/氯苯那敏论文.docx"
    }
  ]
}
```

路径可以是绝对路径，也可以是相对项目工作区或 `knowledge-base/` 的路径。插件会优先尝试解析到真实存在的文件。

## 9. 最小可用示例

AGENTS 工程初期只写这些字段也可以被插件展示：

```json
{
  "project": "DemoProject",
  "workflow": "KnowledgeBuilderWorkflow",
  "agent": "doc-content-analysis",
  "status": "running",
  "message": "正在处理文档",
  "progress": 20
}
```

完成时：

```json
{
  "project": "DemoProject",
  "workflow": "KnowledgeBuilderWorkflow",
  "status": "completed",
  "message": "知识库构建完成",
  "progress": 100,
  "outputs": [
    {
      "label": "知识库目录",
      "path": "WORKSPACE/DemoProject/knowledge-base"
    }
  ]
}
```
