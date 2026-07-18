# Knowledge Builder 工作流

将文档转换为结构化知识库（JSON），支持**增量更新**——新增文档时仅处理差异部分，不重建整个知识库。

---

## 工作流总览

```
用户文档（DOC/DOCX/PDF/TXT）
    │
    ▼ （调度器将文档放入 input/）
┌──────────────────────────────────────────────┐
│  Step 1: doc-content-analysis                 │
│  ┌─────────────────────────────────────────┐  │
│  │  1. doc-convertor：转换 + 内容/图片提取    │  │
│  │  2. AI 总结：生成 summary.json + summary.md │  │
│  │  3. 输出：manifest.json + content_hash   │  │
│  └─────────────────────────────────────────┘  │
│  输出：{workspace}/summary/manifest.json       │
│    每个文档含 content_hash（SHA256）            │
└──────────────────┬───────────────────────────┘
                   │
                   ▼ 读取 manifest.json（含 content_hash）
┌──────────────────────────────────────────────┐
│  Step 2: knowledge-builder（增量构建）          │
│  ┌─────────────────────────────────────────┐  │
│  │  1. 读取 .kb_state.json（如存在）         │  │
│  │  2. 对比 content_hash：                   │  │
│  │     + 新增 → 添加到索引                    │  │
│  │     ~ 变更 → 更新索引                      │  │
│  │     - 删除 → 从索引移除                    │  │
│  │     = 未变更 → 跳过                        │  │
│  │  3. 增量合并关键词/概念索引                │  │
│  │  4. 更新版本号 + 变更日志                  │  │
│  └─────────────────────────────────────────┘  │
│  输出：knowledge-base/                         │
│    ├── .kb_state.json     # 状态（指纹+版本）  │
│    ├── kb-manifest.json   # 总索引             │
│    ├── documents/         # 文档索引            │
│    ├── keywords/          # 关键词索引          │
│    ├── concepts/          # 概念索引            │
│    └── toc.json           # 目录结构            │
└──────────────────────────────────────────────┘
```

---

## 增量更新流程（日常使用）

```
用户新增/修改/删除文档
    │
    ▼
调度器：只将差异文档放入 input/
    │
    ▼
doc-content-analysis 处理差异文档
    ↓ 输出 manifest.json（含 content_hash）
    ↓
kb_manager.py update
    ↓
┌─────────────────────────────────────────┐
│ 对比 manifest vs .kb_state.json          │
│                                         │
│  manifest: [doc_A (hash1), doc_B (hash2)]│
│  state:    [doc_A (hash1), doc_C (hash3)]│
│                                         │
│  → doc_B: 新增（hash2 不在 state 中）    │
│  → doc_C: 删除（state 有但 manifest 无） │
│  → doc_A: 未变更（hash 匹配）            │
└──────────────┬──────────────────────────┘
               │
               ▼
增量合并：
  • 关键词索引：doc_B 的新关键词加入，doc_C 的关键词移除
  • 概念索引：同理增量更新
  • 目录结构：同理增量更新
  • 文档关联：自动更新跨文档引用
    ↓
保存 .kb_state.json（version += 1, change_log += 1）
生成/更新 kb-manifest.json
    ↓
完成——知识库已更新，无需重建
```

---

## Step 1: 文档内容提取（doc-content-analysis）

**Agent**：`doc-content-analysis`
**配置**：`ComponentAgents/doc-content-analysis/AGENT.md`
**Skill**：`doc-convertor` + `img-reader`（可选） + AI 总结

### 输入

```
{workspace}/input/
├── report1.doc          # 旧版 Word
├── report2.docx         # Word
├── paper.pdf            # PDF
└── notes.txt            # 纯文本
```

### 执行

加载 `ComponentAgents/doc-content-analysis/AGENT.md`，按 Step 1 → Step 5b 执行：

1. **初始化工作区**：创建 `{workspace}/converted/` 和 `{workspace}/summary/`
2. **格式转换 + 内容提取**：`doc-convertor` Skill → `{workspace}/converted/` + `{workspace}/summary/*/text/content.json`
3. **图片提取**：`doc-convertor` Skill → `{workspace}/summary/*/img/`
4. **AI 总结**：AI 读取 content.json → 生成 `summary.json` + `summary.md`
5. **图片识别**（可选）：`img-reader` Skill → OCR + AI 视觉总结
6. **生成 manifest.json**：含 `content_hash`（每个 summary.json 的 SHA256）
7. **知识库构建**（调度器触发）：`knowledge-builder` Skill → `knowledge-base/`

### 输出

```
{workspace}/summary/
├── manifest.json              # 处理清单（含 content_hash）
├── report1/
│   └── text/
│       ├── content.json       # 结构化文档内容
│       ├── summary.json       # 结构化索引（含 content_hash）
│       └── summary.md         # 可读总结
├── report2/
│   └── text/
│       ├── content.json
│       ├── summary.json
│       └── summary.md
├── paper/
│   └── text/
│       ├── content.json
│       ├── summary.json
│       └── summary.md
├── notes/
│   └── text/
│       ├── content.json
│       ├── summary.json
│       └── summary.md
├── 综合总结.json
└── 综合总结.md
```

### manifest.json 结构（含 content_hash）

```json
{
  "status": "completed",
  "total_files": 3,
  "success_count": 2,
  "failed_count": 1,
  "documents": [
    {
      "source_file": "report1.doc",
      "status": "success",
      "output_dir": "{workspace}/summary/report1/",
      "content_json": "{workspace}/summary/report1/text/content.json",
      "summary_json": "{workspace}/summary/report1/text/summary.json",
      "summary_md": "{workspace}/summary/report1/text/summary.md",
      "content_hash": "abc123def456789...",
      "image_count": 5,
      "has_img_summary": true
    }
  ],
  "has_combined_summary": true,
  "combined_summary_json": "{workspace}/summary/综合总结.json",
  "combined_summary_md": "{workspace}/summary/综合总结.md",
  "generated_at": "2024-01-01T12:00:00"
}
```

**关键字段**：
- `content_hash`：summary.json 内容的 SHA256 哈希，用于增量检测文档是否变更
- `summary_json`：下游 knowledge-builder 消费的入口文件

---

## Step 2: 知识库构建（knowledge-builder）

**Skill**：`knowledge-builder`
**配置**：`ComponentAgents/doc-content-analysis/SKILLS/knowledge-builder/SKILL.MD`

### 2.1 首次构建（init）

```bash
python ComponentAgents/doc-content-analysis/SKILLS/knowledge-builder/scripts/kb_manager.py init \
  knowledge-base/ \
  {workspace}/summary/ \
  {workspace}/summary/manifest.json
```

**输出**：

```
knowledge-base/
├── .kb_state.json              # 知识库状态
├── kb-manifest.json            # 知识库总索引（入口）
├── documents/                  # 文档索引
│   ├── doc_001.json
│   └── doc_002.json
├── keywords/                   # 关键词索引
│   └── index.json
├── concepts/                   # 核心概念索引
│   └── index.json
└── toc.json                    # 目录结构
```

### 2.2 增量更新（update）— 日常使用

```bash
python ComponentAgents/doc-content-analysis/SKILLS/knowledge-builder/scripts/kb_manager.py update \
  knowledge-base/ \
  {workspace}/summary/ \
  {workspace}/summary/manifest.json
```

**增量更新行为**：

| 场景 | 操作 | 影响范围 |
|------|------|----------|
| 新文档（content_hash 不在 state 中） | 添加到所有索引 | documents/, keywords/, concepts/, toc.json |
| 变更文档（content_hash 不匹配） | 更新索引 | documents/, keywords/, concepts/, toc.json |
| 删除文档（state 中有但 manifest 无） | 从索引移除 | documents/, keywords/, concepts/, toc.json |
| 未变更文档（content_hash 匹配） | 跳过 | 无 |

每个操作记录在 `.kb_state.json` 的 `change_log` 中。

### 2.3 状态查询（status）

```bash
python ComponentAgents/doc-content-analysis/SKILLS/knowledge-builder/scripts/kb_manager.py status \
  knowledge-base/ \
  {workspace}/summary/ \
  {workspace}/summary/manifest.json
```

输出示例：

```
Knowledge Base Status (v3)
  Documents: 12 total
  Keywords:  87
  Concepts:  23
  Last updated: 2024-06-01T12:00:00Z

Pending Changes:
  + New:     2 document(s)
      - doc_report3 (report3.docx)
      - doc_paper2 (paper2.pdf)
  ~ Changed: 1 document(s)
      - doc_report1 (report1.docx)
  - Removed: 0 document(s)
  = Unchanged: 9 document(s)
```

---

## .kb_state.json 结构

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
      "content_hash": "abc123def456...",
      "title": "2024年度报告",
      "added_at": "2024-01-01T12:00:00Z",
      "updated_at": "2024-05-15T08:00:00Z"
    }
  },
  "change_log": [
    {
      "action": "init",
      "version": 1,
      "timestamp": "2024-01-01T12:00:00Z",
      "documents_added": 3,
      "message": "首次全量构建"
    },
    {
      "action": "update",
      "version": 2,
      "timestamp": "2024-02-15T10:00:00Z",
      "new_count": 1,
      "changed_count": 0,
      "removed_count": 0,
      "message": "+1 added"
    },
    {
      "action": "update",
      "version": 3,
      "timestamp": "2024-06-01T12:00:00Z",
      "new_count": 1,
      "changed_count": 1,
      "removed_count": 0,
      "message": "+1 added, ~1 updated"
    }
  ]
}
```

---

## kb-manifest.json 结构（知识库总索引）

```json
{
  "version": 3,
  "name": "knowledge-base",
  "generated_at": "2024-06-01T12:00:00Z",
  "document_count": 5,
  "keyword_count": 42,
  "concept_count": 15,
  "documents": [
    {
      "id": "doc_001",
      "title": "2024年度报告",
      "source_file": "report1.docx",
      "added_at": "2024-01-01T12:00:00Z",
      "updated_at": "2024-05-15T08:00:00Z",
      "content_hash": "abc123...",
      "index_link": "documents/doc_001.json"
    }
  ],
  "top_keywords": [
    {"keyword": "关键词1", "document_count": 3, "total_frequency": 45}
  ],
  "top_concepts": [
    {"concept": "核心概念1", "document_count": 3, "importance": 0.95}
  ],
  "change_log": [
    // 最近 5 条变更记录
  ]
}
```

---

## 使用方式

### 首次使用

```
1. 将所有文档放入 input/
2. 执行 doc-content-analysis（生成 summary/）
3. 执行 kb_manager.py init（首次全量构建）
```

### 日常增量

```
1. 将新增/修改的文档放入 input/
2. 执行 doc-content-analysis（仅分析差异文档）
3. 执行 kb_manager.py update（增量更新知识库）
```

### 文档删除

```
1. 从 input/ 中移除文档
2. 重新执行 doc-content-analysis（manifest 中不再包含该文档）
3. 执行 kb_manager.py update（该文档将从知识库中自动移除）
```

---

## 需求传递流程

当 doc-content-analysis 识别到需求类文档时，自动触发需求传递流程：

```
需求文档（排课要求、表格分析需求等）
    │
    ▼
doc-content-analysis 识别为需求文档
    ↓ summary.json 含 document_type: "requirement"
    ↓
调度器读取 manifest.json
    ↓ 识别 target_agent
    │
    ├─── excel-master（排课/表格分析需求）
    │     input: summary.md
    │     output: 排课 Excel / 分析结果 Excel
    │
    └─── 其他 Agent
```

### 调度器职责

1. 读取 `{workspace}/summary/manifest.json`
2. 检查每个文档的 `document_type` 字段
3. 对于 `requirement` 类型：
   - 读取 `target_agent` 确定目标 Agent
   - 将 `summary.md` 复制到目标 Agent 的 `input/`
   - 调用目标 Agent
4. 同时触发知识库构建（即使有需求文档，知识文档仍需入库）

---

## 错误处理

| 场景 | 处理方式 |
|------|----------|
| doc-content-analysis 未执行 | 提示用户先执行 Step 1 |
| manifest.json status=failed | 读取失败文件的 error，决定跳过或终止 |
| manifest.json status=empty | 告知用户无文件可处理 |
| .kb_state.json 不存在（update 模式） | 自动回退到 init 全量构建 |
| 单文档 summary.json 缺失 | 跳过该文档，记录警告 |
| 知识库目录已存在（init 模式） | 清空后重新构建 |
| 需求文档目标 Agent 不存在 | 记录警告，跳过该需求 |
| content_hash 计算不一致 | 标记文档为变更，重新索引 |
