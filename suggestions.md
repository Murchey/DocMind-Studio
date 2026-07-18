# DocMind-Studio 下一步建议

> 基于项目现状分析，整理优先级建议

---

## 项目现状总结

### 已完成

| 组件 | 状态 | 说明 |
|------|------|------|
| AGENTS.md 调度器 | ✅ 完成 | 工作区初始化、Agent 调度、数据传递规范 |
| doc-content-analysis | ✅ 完成 | 含 doc-convertor、img-reader、knowledge-builder 三个 SKILL |
| doc-form-master | ✅ 完成 | 含 20+ SKILL，覆盖格式化全流程 |
| excel-master | ⚠️ 部分完成 | 有 13 个 SKILL 目录，但缺 SKILL.md |
| ppt-deep-summary | ✅ 完成 | 含 PPTParser、PPTAnalyst、PPTIntelligent、PPTFormatting |
| ppt-continuation-tool | ✅ 完成 | 含 continuation-analyzer、continuation-filler、pptx-preview |
| phd-research-agent | ⚠️ 部分完成 | 有 SKILL.md 但无 scripts |
| ppt-master-main | ⚠️ 独立项目 | 有完整文档，需整合 |
| process-skill | ✅ 完成 | 进度追踪，供插件使用 |
| KnowledgeBuilder 工作流 | ✅ 完成 | 详细文档 + knowledge-builder SKILL 已实现 |
| AcademicDocs 工作流 | ❌ 仅标题 | 需补充完整流程 |
| EnterpriseDocs 工作流 | ❌ 仅标题 | 需补充完整流程 |
| VS Code 插件 | ⚠️ 部分完成 | Extension 目录已有基础框架 |

### 缺失组件

| 组件 | 优先级 | 说明 |
|------|--------|------|
| excel-master SKILL.md | 🔴 高 | 13 个 SKILL 缺统一入口 |
| AcademicDocs 工作流 | 🔴 高 | 仅 6 行内容，无实际流程 |
| EnterpriseDocs 工作流 | 🔴 高 | 仅标题，无内容 |
| phd-research-agent 脚本 | 🟡 中 | SKILL.md 存在但无 Python 实现 |
| ppt-master-main 整合 | 🟡 中 | 独立项目需与主项目对接 |

---

## 完成度评估

### 整体完成度：**65%**

**核心能力已具备**：
- ✅ 知识库构建（含增量更新）已完整实现
- ✅ 文档格式化能力完整
- ✅ PPT 深度分析和续写能力完整
- ✅ 进度追踪机制完整
- ✅ 工作区调度规范完整

**关键阻塞点**：
- ❌ 学术/企业工作流未定义
- ❌ excel-master 缺统一入口
- ❌ 端到端测试缺失

---

## 优先级建议

### P0：阻塞性问题（立即处理）

#### 1. 完善 AcademicDocs 工作流

**问题**：当前只有 6 行内容，无实际流程定义。

**建议**：基于现有 Agent 能力，补充完整流程：

```
用户需求 → 需求分析
    ↓
材料提取（doc-content-analysis）
    ↓
论文评审（phd-research-agent）
    ↓
格式标准化（doc-form-master）
    ↓
知识库构建（KnowledgeBuilderWorkflow）
    ↓
输出到工作区
```

**核心步骤**：
1. 文档格式检测（中文/英文论文）
2. 模板选择与应用
3. 格式标准化（页边距、字体、行距）
4. 公式保护
5. 参考文献处理
6. 目录生成
7. PDF 导出

---

#### 2. 完善 EnterpriseDocs 工作流

**问题**：当前只有 1 行标题。

**建议**：基于现有 Agent 能力，补充完整流程：

```
会议纪要/报告 → 内容提取（doc-content-analysis）
    ↓
表格数据对比（excel-master）
    ↓
研究报告生成（report-generator）
    ↓
汇报PPT生成（ppt-master）
    ↓
知识库构建（KnowledgeBuilderWorkflow）
    ↓
输出到工作区
```

**核心步骤**：
1. 会议纪要整理
2. 表格数据对比与可视化
3. 报告生成
4. PPT 汇报生成

---

#### 3. 补充 excel-master 的 SKILL.md

**问题**：skills 目录下有 13 个子目录，但缺少统一的 SKILL.md 入口文件。

**建议**：创建 `ComponentAgents/excel-master-main/skills/SKILL.md`，包含：
- 13 个 SKILL 列表和触发条件
- 工作流依赖图
- 调用示例（多表格对比、图表生成、排课等）

---

### P1：高优先级（本周完成）

#### 4. 端到端测试

**目标**：验证完整工作流能否正常运行。

**测试场景**：
- [ ] KnowledgeBuilder：3 个 DOCX → 知识库（含增量更新）
- [ ] AcademicDocs：MD → 格式化论文（需先完善工作流）
- [ ] EnterpriseDocs：Excel + 会议纪要 → 报告（需先完善工作流）
- [ ] PPT 续写：半完成 PPT + 资料 → 完整 PPT

---

#### 5. 补充 phd-research-agent 脚本

**问题**：有 SKILL.md（pre-submission-reviewer、intro-drafter、idea-evaluator）但无 Python 脚本。

**建议**：评估是否需要脚本实现，或保持 AI 原生模式（当前 phd-research-agent 可能依赖 LLM 直接推理）。

---

#### 6. ppt-master-main 整合

**问题**：独立项目，需与主项目整合。

**建议**：
- 确认 `skills/ppt-master/SKILL.md` 作为主入口
- 在 AGENTS.md 中完善调度方式
- 测试从主项目调用 ppt-master 的完整流程

---

### P2：中优先级（两周内完成）

#### 7. VS Code 插件完善

**现状**：Extension 目录已有基础框架（providers、webview）

**建议**：
- 完成 dashboardPanel.ts 实现
- 实现工作流配置可视化
- 实现进度实时显示（读取 `.docmind-progress.json`）
- 实现输出预览

---

#### 8. 工作流配置化

**目标**：将硬编码的工作流逻辑提取为可配置文件。

**建议**：
- 定义工作流 JSON Schema
- 支持用户自定义工作流
- 工作流导入/导出

---

## 快速行动清单

### 本周必做

- [ ] 完善 `AcademicDocsWorkflow.md`（基于现有 Agent 能力）
- [ ] 完善 `EnterpriseDocsWorkflow.md`（基于现有 Agent 能力）
- [ ] 创建 `excel-master` 的 `SKILL.md`
- [ ] 端到端测试 KnowledgeBuilder 工作流

### 下周必做

- [ ] phd-research-agent 脚本评估
- [ ] ppt-master-main 整合测试
- [ ] VS Code 插件功能完善

### 持续改进

- [ ] 文档补充（每个 SKILL 的使用示例）
- [ ] 错误处理完善
- [ ] 日志规范统一

---

## 依赖关系图

```
KnowledgeBuilderWorkflow (已完成)
    │
    ├── doc-content-analysis (已完成)
    └── knowledge-builder (已完成)

AcademicDocsWorkflow (P0 需完善)
    │
    ├── doc-content-analysis (已完成)
    ├── phd-research-agent (部分完成)
    ├── doc-form-master (已完成)
    └── KnowledgeBuilderWorkflow (已完成)

EnterpriseDocsWorkflow (P0 需完善)
    │
    ├── doc-content-analysis (已完成)
    ├── excel-master (部分完成)
    ├── ppt-master (待整合)
    └── KnowledgeBuilderWorkflow (已完成)
```

---

## 建议负责人

| 任务 | 建议 | 原因 |
|------|------|------|
| 工作流完善 | AI | 基于现有 Agent 能力编写流程 |
| excel-master SKILL.md | 开发 | 需要确认现有 SKILL 的实际功能 |
| 端到端测试 | 开发 | 需要运行环境和测试数据 |
| VS Code 插件 | 开发 | 需要前端开发能力 |
| phd-research-agent 脚本 | AI + 开发协作 | 评估是否需要脚本实现 |

---

## 更新说明

**2026-07-18 更新**：
- knowledge-builder 已实现（原 P0 任务已完成）
- 工作流完成度重新评估：KnowledgeBuilder 65% → 实际完成度更高
- 新增 P0 任务：完善 AcademicDocs/EnterpriseDocs 工作流
- 新增 P0 任务：补充 excel-master SKILL.md
- 调整优先级：工作流定义优先于脚本实现
