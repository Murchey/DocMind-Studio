---
name: knowledge-builder
description: 知识库构建与管理，支持增量更新、文档差异检测、关键词与概念索引合并
tools: [python]
---

# Knowledge Builder

知识库构建与管理 Skill。支持三种运行模式：首次全量构建、增量更新、状态查询。

## 功能说明

将 `doc-content-analysis` 输出的结构化总结（summary.json）聚合为可查询的知识库，支持：
- **增量更新**：仅处理新增/变更的文档，不重建整个知识库
- **文档指纹**：通过内容哈希检测文档是否变更
- **索引合并**：关键词和概念索引支持增量添加和频率更新
- **变更日志**：记录每次更新操作

## 输入/输出

**输入**：
- `doc-content-analysis` 的 `summary/manifest.json`
- `doc-content-analysis` 的 `summary/<文档>/text/summary.json`

**输出**：
- `knowledge-base/` 目录，包含完整的知识库结构

## 知识库目录结构

```
knowledge-base/
├── .kb_state.json            # 知识库状态（文档指纹、版本号、变更日志）
├── kb-manifest.json          # 知识库总索引（入口）
├── documents/                # 文档索引
│   ├── doc_001.json
│   └── doc_002.json
├── keywords/                 # 关键词索引
│   └── index.json
├── concepts/                 # 核心概念索引
│   └── index.json
└── toc.json                  # 目录结构
```

### .kb_state.json 结构

```json
{
  "version": 3,
  "created_at": "2024-01-01T12:00:00Z",
  "updated_at": "2024-06-01T12:00:00Z",
  "document_count": 5,
  "keyword_count": 42,
  "concept_count": 15,
  "documents": {
    "doc_001": {
      "source_file": "report1.docx",
      "content_hash": "abc123...",
      "title": "报告标题",
      "added_at": "2024-01-01T12:00:00Z",
      "updated_at": "2024-05-15T08:00:00Z"
    }
  },
  "change_log": [
    {
      "action": "init",
      "version": 1,
      "timestamp": "2024-01-01T12:00:00Z",
      "message": "首次全量构建"
    }
  ]
}
```

## 运行模式

### 1. init — 首次全量构建

```bash
python SKILLS/knowledge-builder/scripts/kb_manager.py init \
  knowledge-base/ \
  workspace/summary/ \
  workspace/summary/manifest.json
```

### 2. update — 增量更新（推荐日常使用）

```bash
python SKILLS/knowledge-builder/scripts/kb_manager.py update \
  knowledge-base/ \
  workspace/summary/ \
  workspace/summary/manifest.json
```

`update` 模式自动：
- 检测 `.kb_state.json` 是否存在，不存在则回退到 `init`
- 对比 manifest.json 与 state，识别新增/变更/删除的文档
- 仅处理差异文档
- 增量合并关键词和概念索引
- 更新跨文档关联
- 版本号 +1
- 追加变更日志

### 3. status — 状态查询

```bash
python SKILLS/knowledge-builder/scripts/kb_manager.py status \
  knowledge-base/ \
  workspace/summary/ \
  workspace/summary/manifest.json
```

输出当前知识库状态和待处理的差异预览。

## 增量更新原理

```
新文档到达
    ↓
doc-content-analysis 处理新文档
    ↓ 生成 summary.json + manifest.json
    ↓
kb_manager.py update
    ↓
读取 .kb_state.json（已有文档指纹）
    ↓
对比 manifest.json 中的文档 vs state 中的文档
    ├── 新增（content_hash 不在 state 中）→ 添加到索引
    ├── 变更（content_hash 不匹配）     → 更新索引
    ├── 未变更（content_hash 匹配）      → 跳过
    └── 删除（state 中有但 manifest 无） → 从索引移除
    ↓
增量合并关键词/概念索引，更新频率
    ↓
保存 .kb_state.json（新版本号 + 变更日志）
```

## 方法参考

| 方法 | 说明 |
|------|------|
| `cmd_init(kb_dir, summary_dir, manifest_path)` | 首次全量构建 |
| `cmd_update(kb_dir, summary_dir, manifest_path)` | 增量更新 |
| `cmd_status(kb_dir, summary_dir, manifest_path)` | 状态查询 |
| `_diff_documents(manifest_docs, state, summary_dir)` | 文档差异检测 |
| `_merge_keywords(existing_index, new_summaries, removed_ids)` | 关键词增量合并 |
| `_merge_concepts(existing_index, new_summaries, removed_ids)` | 概念增量合并 |
| `_merge_toc(existing_toc, new_summaries, removed_ids)` | 目录增量合并 |

## 错误处理

- manifest 状态不是 `completed` → 报错退出
- .kb_state.json 不存在时执行 update → 自动回退到 init
- 无差异时执行 update → 输出提示并跳过
