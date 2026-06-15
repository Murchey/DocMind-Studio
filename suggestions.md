# DocMind-Studio 下一步建议

> 基于项目现状分析，整理优先级建议

---

## 项目现状总结

### 已完成

| 组件 | 状态 | 说明 |
|------|------|------|
| AGENTS.md 调度器 | ✅ 完成 | 工作区初始化、Agent 调度、数据传递规范 |
| doc-content-analysis | ✅ 完成 | 含 doc-convertor、img-reader 两个 SKILL |
| doc-form-master | ✅ 完成 | 含 20+ SKILL，覆盖格式化全流程 |
| excel-master | ⚠️ 部分完成 | 有 13 个 SKILL 目录，但缺 SKILL.md |
| ppt-deep-summary | ✅ 完成 | 含 PPTParser、PPTAnalyst、PPTIntelligent、PPTFormatting |
| ppt-continuation-tool | ✅ 完成 | 含 continuation-analyzer、continuation-filler、pptx-preview |
| phd-research-agent | ⚠️ 部分完成 | 有 SKILL.md 但无 scripts |
| ppt-master-main | ⚠️ 独立项目 | 有完整文档，需整合 |
| process-skill | ✅ 完成 | 进度追踪，供插件使用 |
| KnowledgeBuilder 工作流 | ✅ 完成 | 详细文档 |
| AcademicDocs 工作流 | ❌ 仅标题 | 需补充完整流程 |
| EnterpriseDocs 工作流 | ❌ 仅标题 | 需补充完整流程 |

### 缺失组件

| 组件 | 优先级 | 说明 |
|------|--------|------|
| knowledge-builder Agent | 🔴 高 | KnowledgeBuilder 工作流的核心，但无 Agent 实现 |
| VS Code 插件 | 🟡 中 | 分工方案中提到，尚未开始 |

---

## 优先级建议

### P0：阻塞性问题（立即处理）

#### 1. 创建 knowledge-builder Agent

**问题**：KnowledgeBuilder 工作流依赖此 Agent，但 ComponentAgents 下无对应实现。

**建议**：
```
ComponentAgents/knowledge-builder/
├── AGENT.md            # Agent 配置
├── SKILLS/
│   └── kb-aggregator/
│       ├── SKILL.MD    # 聚合逻辑说明
│       └── scripts/
│           └── kb_aggregator.py  # 索引聚合脚本
└── requirements.txt
```

**核心功能**：
- 读取 `doc-content-analysis` 输出的 `summary.json`
- 构建 `kb-manifest.json`（知识库总索引）
- 生成 `documents/`、`keywords/`、`concepts/` 索引
- 生成 `toc.json`（目录结构）

---

### P1：高优先级（本周完成）

#### 2. 补充 excel-master 的 SKILL.md

**问题**：skills 目录下有 13 个子目录，但缺少统一的 SKILL.md 入口文件。

**建议**：创建 `ComponentAgents/excel-master-main/skills/SKILL.md`，包含：
- Skill 列表和触发条件
- 工作流依赖图
- 调用示例

#### 3. 完善 AcademicDocs 工作流

**问题**：当前只有 6 行内容，无实际流程定义。

**建议**：补充完整的学术文档处理流程：
- 文档格式检测
- 模板选择（中文论文/英文论文）
- 格式标准化
- 公式保护
- 参考文献处理
- 目录生成
- PDF 导出

#### 4. 完善 EnterpriseDocs 工作流

**问题**：当前只有 1 行标题。

**建议**：补充企业文档处理流程：
- 会议纪要整理
- 表格数据对比
- 报告生成
- PPT 汇报生成

---

### P2：中优先级（两周内完成）

#### 5. 端到端测试

**目标**：验证完整工作流能否正常运行。

**测试场景**：
- [ ] KnowledgeBuilder：3 个 DOCX → 知识库
- [ ] AcademicDocs：MD → 格式化论文
- [ ] EnterpriseDocs：Excel + 会议纪要 → 报告
- [ ] PPT 续写：半完成 PPT + 资料 → 完整 PPT

#### 6. 补充 phd-research-agent 脚本

**问题**：有 SKILL.md（pre-submission-reviewer、intro-drafter、idea-evaluator）但无 Python 脚本。

**建议**：评估是否需要脚本实现，或保持 AI 原生模式。

#### 7. ppt-master-main 整合

**问题**：独立项目，需与主项目整合。

**建议**：
- 确认 `skills/ppt-master/SKILL.md` 作为主入口
- 在 AGENTS.md 中完善调度方式
- 测试从主项目调用 ppt-master 的完整流程

---

### P3：低优先级（后续迭代）

#### 8. VS Code 插件开发

**目标**：配合 DocMind-Studio 的专属插件。

**功能规划**：
- 工作流配置可视化
- 进度实时显示（读取 `.docmind-progress.json`）
- 输出预览
- 快速创建工作流

#### 9. 工作流配置化

**目标**：将硬编码的工作流逻辑提取为可配置文件。

**建议**：
- 定义工作流 JSON Schema
- 支持用户自定义工作流
- 工作流导入/导出

---

## 快速行动清单

### 本周必做

- [ ] 创建 `knowledge-builder` Agent 骨架
- [ ] 补充 `excel-master` 的 SKILL.md
- [ ] 完善 `AcademicDocsWorkflow.md`
- [ ] 完善 `EnterpriseDocsWorkflow.md`

### 下周必做

- [ ] knowledge-builder 核心脚本开发
- [ ] 端到端测试（KnowledgeBuilder 工作流）
- [ ] phd-research-agent 脚本评估

### 持续改进

- [ ] 文档补充（每个 SKILL 的使用示例）
- [ ] 错误处理完善
- [ ] 日志规范统一

---

## 依赖关系图

```
knowledge-builder (P0)
    ↑
    │ 依赖
    │
doc-content-analysis (已完成)
    ↑
    │ 输出
    │
用户文档

AcademicDocs 工作流 (P1)
    ↑
    │ 使用
    │
doc-form-master (已完成)

EnterpriseDocs 工作流 (P1)
    ↑
    │ 使用
    │
excel-master (P1 补充 SKILL.md)
```

---

## 建议负责人

| 任务 | 建议 | 原因 |
|------|------|------|
| knowledge-builder | AI + 开发协作 | 需要理解 doc-content-analysis 输出格式 |
| excel-master SKILL.md | 开发 | 需要确认现有 SKILL 的实际功能 |
| 工作流完善 | AI | 基于现有 Agent 能力编写流程 |
| VS Code 插件 | 开发 | 需要前端开发能力 |
