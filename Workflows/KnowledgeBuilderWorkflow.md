# Knowledge Builder 工作流

将多个文档转换为结构化知识库（JSON），供 AI 通过 Agent 调用和使用。

---

## 工作流总览

```
用户文档（DOC/DOCX/PDF/TXT）
    │
    ▼
┌─────────────────────────────┐
│  Step 1: doc-content-analysis│  文档转换 + 内容提取 + AI 总结
│  输入：workspace/input/      │
│  输出：workspace/summary/    │
│    ├── manifest.json         │
│    └── <文件名>/text/        │
│        ├── content.json      │  结构化文档内容
│        └── summary.json      │  结构化索引（含关键词、链接、位置）
└─────────────┬───────────────┘
              │
              ▼
┌─────────────────────────────┐
│  Step 2: knowledge-builder   │  索引聚合 + 知识库构建
│  输入：summary/manifest.json │
│  输出：knowledge-base/       │
│    ├── kb-manifest.json      │  知识库总索引
│    ├── documents/            │  文档索引
│    ├── keywords/             │  关键词索引
│    ├── concepts/             │  核心概念索引
│    └── toc.json              │  目录结构
└─────────────────────────────┘
```

---

## Step 1: 文档内容提取（doc-content-analysis）

**Agent**：`doc-content-analysis`
**配置**：`ComponentAgents/doc-content-analysis/AGENT.md`

### 输入

```
doc-content-analysis/workspace/input/
├── report1.doc
├── report2.docx
├── paper.pdf
└── notes.txt
```

### 执行

加载 `ComponentAgents/doc-content-analysis/AGENT.md`，按 Step 1 → Step 5 执行。

### 输出

```
doc-content-analysis/workspace/summary/
├── manifest.json                    # 处理清单
├── report1/
│   └── text/
│       ├── content.json             # 结构化文档内容
│       └── summary.json             # 结构化索引
├── report2/
│   └── text/
│       ├── content.json
│       └── summary.json
├── paper/
│   └── text/
│       ├── content.json
│       └── summary.json
├── notes/
│   └── text/
│       ├── content.json
│       └── summary.json
└── 综合总结.json
```

**关键输出**：每个文档的 `summary.json` 包含：
- `id`：文档唯一标识
- `keywords`：关键词列表（含词频、相关度）
- `sections`：章节结构（含 content_link）
- `key_info`：关键信息（含位置标注）
- `content_links`：内容链接

---

## Step 2: 知识库构建（knowledge-builder）

**处理方式：AI 原生（无需 Python 脚本）**

AI 助手读取 `doc-content-analysis` 的输出，构建结构化知识库。

### 2.1 读取输入

读取 `doc-content-analysis/workspace/summary/manifest.json`，获取所有文档的处理结果。

对每个成功处理的文档，读取其 `summary.json` 索引文件。

### 2.2 构建知识库目录结构

在项目根目录创建 `knowledge-base/`：

```
knowledge-base/
├── kb-manifest.json           # 知识库总索引（入口）
├── documents/                 # 文档索引
│   ├── doc_001.json           # 文档 1 的完整索引
│   ├── doc_002.json           # 文档 2 的完整索引
│   └── doc_003.json
├── keywords/                  # 关键词索引
│   ├── index.json             # 关键词 → 文档映射
│   └── <keyword>.json         # 单个关键词的详细索引
├── concepts/                  # 核心概念索引
│   ├── index.json             # 概念 → 文档映射
│   └── <concept>.json         # 单个概念的详细索引
└── toc.json                   # 文档目录结构（篇目）
```

### 2.3 生成 kb-manifest.json（知识库总索引）

```json
{
  "version": "1.0",
  "name": "knowledge-base",
  "generated_at": "2024-01-01T12:00:00",
  "document_count": 4,
  "keyword_count": 50,
  "concept_count": 20,

  "documents": [
    {
      "id": "doc_001",
      "title": "报告标题",
      "source_file": "report1.doc",
      "author": "作者",
      "language": "zh",
      "summary": "一段话概述...",
      "keywords": ["关键词1", "关键词2"],
      "sections_count": 5,
      "content_link": "doc-content-analysis/workspace/summary/report1/text/content.json",
      "index_link": "documents/doc_001.json"
    }
  ],

  "top_keywords": [
    {"keyword": "关键词1", "document_count": 3, "total_frequency": 45},
    {"keyword": "关键词2", "document_count": 2, "total_frequency": 28}
  ],

  "top_concepts": [
    {"concept": "核心概念1", "document_count": 3, "importance": 0.95},
    {"concept": "核心概念2", "document_count": 2, "importance": 0.87}
  ]
}
```

### 2.4 生成文档索引（documents/）

每个文档生成 `documents/<id>.json`，扩展自 doc-content-analysis 的 summary.json：

```json
{
  "id": "doc_001",
  "title": "报告标题",
  "source_file": "report1.doc",
  "author": "作者",
  "language": "zh",
  "generated_at": "2024-01-01T12:00:00",

  "summary": "文档摘要...",

  "keywords": [
    {"keyword": "关键词1", "frequency": 12, "relevance": 0.95}
  ],

  "sections": [
    {
      "heading": "章节标题",
      "level": 2,
      "paragraph_range": [1, 15],
      "key_points": ["要点1", "要点2"],
      "content_link": "doc-content-analysis/workspace/summary/report1/text/content.json#/paragraphs/0-14"
    }
  ],

  "key_info": {
    "data": [{"value": "关键数据", "location": "paragraph_5"}],
    "conclusions": [{"text": "核心观点", "location": "paragraph_12"}],
    "references": [{"text": "重要引用", "location": "paragraph_20"}]
  },

  "tables": [
    {
      "index": 0,
      "description": "表格描述",
      "location": "paragraph_8",
      "content_link": "doc-content-analysis/workspace/summary/report1/text/content.json#/tables/0"
    }
  ],

  "images": [
    {
      "file": "image_1.png",
      "path": "doc-content-analysis/workspace/summary/report1/img/image_1.png",
      "description": "图片描述",
      "ocr_link": "doc-content-analysis/workspace/summary/report1/img/text/image_1.txt",
      "summary_link": "doc-content-analysis/workspace/summary/report1/img/img-summary/image_1.md"
    }
  ],

  "content_links": {
    "content_json": "doc-content-analysis/workspace/summary/report1/text/content.json",
    "summary_md": "doc-content-analysis/workspace/summary/report1/text/summary.md",
    "images_dir": "doc-content-analysis/workspace/summary/report1/img/"
  },

  "related_documents": [
    {"id": "doc_002", "relation": "共同主题", "shared_keywords": ["关键词1"]}
  ]
}
```

### 2.5 生成关键词索引（keywords/）

`keywords/index.json` — 关键词到文档的映射：

```json
{
  "generated_at": "2024-01-01T12:00:00",
  "total_keywords": 50,
  "keywords": [
    {
      "keyword": "关键词1",
      "total_frequency": 45,
      "document_count": 3,
      "documents": [
        {"id": "doc_001", "frequency": 12, "relevance": 0.95},
        {"id": "doc_002", "frequency": 20, "relevance": 0.90},
        {"id": "doc_003", "frequency": 13, "relevance": 0.85}
      ],
      "detail_link": "keywords/关键词1.json"
    }
  ]
}
```

`keywords/<keyword>.json` — 单个关键词详情：

```json
{
  "keyword": "关键词1",
  "total_frequency": 45,
  "document_count": 3,
  "documents": [
    {
      "id": "doc_001",
      "title": "报告标题",
      "frequency": 12,
      "relevance": 0.95,
      "locations": ["paragraph_3", "paragraph_8", "paragraph_15"],
      "context_snippets": ["包含关键词的上下文片段..."]
    }
  ],
  "related_keywords": ["相关词1", "相关词2"]
}
```

### 2.6 生成核心概念索引（concepts/）

`concepts/index.json` — 概念到文档的映射：

```json
{
  "generated_at": "2024-01-01T12:00:00",
  "total_concepts": 20,
  "concepts": [
    {
      "concept": "核心概念1",
      "definition": "概念定义...",
      "importance": 0.95,
      "document_count": 3,
      "documents": ["doc_001", "doc_002", "doc_003"],
      "detail_link": "concepts/核心概念1.json"
    }
  ]
}
```

`concepts/<concept>.json` — 单个概念详情：

```json
{
  "concept": "核心概念1",
  "definition": "概念定义...",
  "importance": 0.95,
  "document_count": 3,
  "occurrences": [
    {
      "document_id": "doc_001",
      "document_title": "报告标题",
      "locations": [
        {"section": "章节标题", "paragraph": 5, "snippet": "概念出现的上下文..."}
      ]
    }
  ],
  "related_concepts": ["相关概念1", "相关概念2"],
  "related_keywords": ["关键词1", "关键词2"]
}
```

### 2.7 生成目录结构（toc.json）

```json
{
  "generated_at": "2024-01-01T12:00:00",
  "document_count": 4,
  "toc": [
    {
      "id": "doc_001",
      "title": "报告标题",
      "source_file": "report1.doc",
      "sections": [
        {
          "heading": "第一章 引言",
          "level": 1,
          "paragraph_range": [1, 20],
          "children": [
            {
              "heading": "1.1 背景",
              "level": 2,
              "paragraph_range": [1, 10]
            },
            {
              "heading": "1.2 目的",
              "level": 2,
              "paragraph_range": [11, 20]
            }
          ]
        }
      ]
    }
  ]
}
```

---

## 输出规范

### 知识库入口

调度器/下游 Agent 通过 `knowledge-base/kb-manifest.json` 进入知识库。

### 使用方式

1. 读取 `kb-manifest.json` 获取文档列表和关键词/概念概览
2. 读取 `documents/<id>.json` 获取单文档详细索引
3. 读取 `keywords/index.json` 按关键词查找相关文档
4. 读取 `concepts/index.json` 按概念查找相关文档
5. 通过 `content_link` 追溯到原始内容（content.json）
6. 通过 `toc.json` 浏览文档目录结构

### 状态流转

```
doc-content-analysis 完成
    ↓ 读取 manifest.json
    ↓ status == "completed"
knowledge-builder 开始
    ↓ 读取所有 summary.json
    ↓ 构建知识库
    ↓ 生成 kb-manifest.json
知识库就绪
    ↓ 下游 Agent 可消费
```

---

## 需求传递流程

当 doc-content-analysis 识别到需求类文档时，自动触发需求传递流程：

### 需求识别

doc-content-analysis 在 Step 4 识别文档类型：
- **知识文档**：进入标准知识库构建流程
- **需求文档**：进入需求传递流程

### 需求文档处理

```
需求文档（排课要求、表格分析需求等）
    │
    ▼
┌─────────────────────────────┐
│  doc-content-analysis       │
│  Step 4: 识别为需求文档      │
│  输出：summary.json/md      │
│    ├── document_type: "requirement"
│    ├── requirement_type: "schedule" | "excel"
│    └── target_agent: "schedule-agent" | "excel-master"
└─────────────┬───────────────┘
              │
              ▼
┌─────────────────────────────┐
│  调度器读取 manifest.json    │
│  识别需求类型和目标 Agent    │
└─────────────┬───────────────┘
              │
              ├─── schedule-agent ───┐
              │                      ▼
              │    ┌─────────────────────────────┐
              │    │  schedule-agent             │
              │    │  input: summary.md          │
              │    │  output: 课表 Excel         │
              │    └─────────────────────────────┘
              │
              └─── excel-master ─────┐
                                     ▼
                   ┌─────────────────────────────┐
                   │  excel-master               │
                   │  input: summary.md          │
                   │  output: 分析结果 Excel     │
                   └─────────────────────────────┘
```

### 调度器职责

1. 读取 `doc-content-analysis/workspace/summary/manifest.json`
2. 检查每个文档的 `document_type` 字段
3. 对于 `document_type: "requirement"` 的文档：
   - 读取 `target_agent` 字段确定目标 Agent
   - 将 `summary.md` 复制到目标 Agent 的 `input/` 目录
   - 调用目标 Agent 执行任务

### 需求传递示例

```python
# 调度器读取 manifest
with open('doc-content-analysis/workspace/summary/manifest.json', 'r') as f:
    manifest = json.load(f)

for doc in manifest['documents']:
    if doc.get('document_type') == 'requirement':
        target_agent = doc.get('target_agent')
        summary_md = doc['summary_md']
        
        # 复制到目标 Agent
        if target_agent == 'schedule-agent':
            shutil.copy(summary_md, 'schedule-agent/workspace/input/需求.md')
            # 调用 schedule-agent
        elif target_agent == 'excel-master':
            shutil.copy(summary_md, 'excel-master/workspace/input/需求.md')
            # 调用 excel-master
```

---

## 错误处理

| 场景 | 处理方式 |
|------|----------|
| doc-content-analysis 未执行 | 提示用户先执行 Step 1 |
| manifest.json status=failed | 读取失败文件的 error，决定跳过或终止 |
| manifest.json status=empty | 告知用户无文件可处理 |
| 单文档 summary.json 缺失 | 跳过该文档，在 kb-manifest.json 中标记 |
| 知识库目录已存在 | 清空后重新构建 |
| 需求文档目标 Agent 不存在 | 记录警告，跳过该需求 |
| 需求文档格式不规范 | 尝试解析，记录警告 |
