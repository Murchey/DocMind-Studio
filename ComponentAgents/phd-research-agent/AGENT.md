---
name: phd-research-agent
description: 科研辅助 Agent，提供 Idea 评估、Introduction 草稿、论文审阅等核心能力
tools: [markdown]
input: WORKSPACE/{ProjectName}/phd-research-agent/input/（调度器放置的研究想法或论文草稿）
output: WORKSPACE/{ProjectName}/phd-research-agent/summary/（结构化的评估报告或写作建议）
---

# PhD Research Agent

## 多 Agent 集成契约

### 调用接口
调度器通过读取本 AGENT.md 并执行工作流来触发本 Agent。调度器负责创建工作区并将工作区路径传入。

### 输入契约
- 路径：`{workspace}/input/`（调度器传入的工作区路径下）
- 格式：Markdown 或纯文本
- 命名规范：`<task_type>.md`（如 `idea.md`, `draft.md`）

### 输出契约
- 路径：`{workspace}/summary/`
- 格式：结构化 JSON + 可读 MD
- manifest.json：处理清单
- 核心输出：评估报告或写作建议

## 工作区规则

**工作区路径**：由调度器创建并传入，位于 `WORKSPACE/{ProjectName}/phd-research-agent/`

**目录结构**：
```
WORKSPACE/{ProjectName}/phd-research-agent/
├── input/                  # 输入（只读，调度器放置）
└── summary/                # 最终输出
    ├── manifest.json       # 处理清单
    ├── <task_type>_result.json
    └── <task_type>_result.md
```

**约束**：
- 工作区是 SKILL 输出的唯一存放位置
- `input/` 只读，Agent 不修改
- 每次任务开始时清空 `summary/` 目录

## 执行流程

### Step 1: 任务识别
- **目的**：识别用户输入的任务类型
- **判断逻辑**：
  - 如果输入包含研究想法 → 使用 `idea-evaluator`
  - 如果输入包含论文草稿且需要审阅 → 使用 `pre-submission-reviewer`
  - 如果需要起草 Introduction → 使用 `intro-drafter`

### Step 2: 调用对应 SKILL
- **调用的 SKILL**：根据任务类型读取对应的 SKILL.MD
- **代码示例**：
  ```python
  # 读取 SKILL 文件
  with open(f"SKILLS/{skill_name}/SKILL.md", "r") as f:
      skill_content = f.read()
  
  # 执行 SKILL 中定义的流程
  result = execute_skill(skill_content, input_data)
  ```

### Step 3: 生成输出
- **输出位置**：`{workspace}/summary/`（调度器传入的工作区路径下）
- **输出内容**：
  - `manifest.json`：处理清单
  - `<task_type>_result.json`：结构化结果
  - `<task_type>_result.md`：可读报告

### Step 4: 知识库注册（可选）
- **目的**：将本 Agent 的分析结果注册到项目知识库，供其他 Agent 查询引用
- **执行命令**：
  ```bash
  python SKILLS/knowledge-builder/scripts/kb_manager.py register \
    {workspace}/../knowledge-base/ \
    phd-research-agent \
    {workspace}/summary/manifest.json \
    --summary-dir {workspace}/summary/
  ```
- **说明**：注册后知识库可被下游 Agent（如 ppt-master）检索和引用

## 核心规则

### 处理规则
1. 严格按照 SKILL.MD 中定义的步骤执行
2. 每个步骤完成后记录中间结果
3. 遇到致命缺陷时短路返回

### 输出规则
1. JSON 格式使用 `indent=2` 格式化
2. 包含 `source_file` 字段（可追溯）
3. 包含 `generated_at` 字段（ISO 8601 时间戳）
4. 使用 UTF-8 编码

### 错误处理
1. 输入文件不存在 → 返回 `status: "empty"`
2. SKILL 执行失败 → 返回 `status: "failed"` + 错误信息
3. 部分成功 → 返回 `status: "completed"` + 详细统计

## 可用 SKILLS

| SKILL | 功能 | 触发条件 |
|-------|------|----------|
| idea-evaluator | 评估研究想法 | 用户提出研究想法 |
| intro-drafter | 起草 Introduction | 需要论文 Introduction |
| pre-submission-reviewer | 论文审阅 | 提交前审阅 |

## 输出示例

> 以下路径中 `{workspace}` 表示调度器传入的工作区绝对路径，如 `WORKSPACE/ChlorphenaminePaper/phd-research-agent/`

### manifest.json
```json
{
  "status": "completed",
  "total_files": 1,
  "success_count": 1,
  "failed_count": 0,
  "documents": [
    {
      "source_file": "idea.md",
      "status": "success",
      "output_dir": "{workspace}/summary/",
      "result_json": "{workspace}/summary/idea_result.json",
      "result_md": "{workspace}/summary/idea_result.md"
    }
  ],
  "generated_at": "2026-06-09T12:00:00"
}
```

### idea_result.json
```json
{
  "source_file": "idea.md",
  "generated_at": "2026-06-09T12:00:00",
  "verdict": "Accept with Revisions",
  "scores": {
    "higher": 4,
    "faster": 3,
    "stronger": 5,
    "cheaper": 2,
    "broader": 4
  },
  "fatal_flaws": [],
  "suggestions": ["建议1", "建议2"]
}
```

### intro_outline.json
```json
{
  "source_file": "research_info.md",
  "generated_at": "2026-06-09T12:00:00",
  "paragraphs": [
    {"purpose": "背景介绍", "content": "介绍研究领域的重要性和研究对象"},
    {"purpose": "现有工作", "content": "总结现有方法及其局限性"},
    {"purpose": "问题本质", "content": "明确核心问题和研究目标"},
    {"purpose": "关键挑战", "content": "列出技术难点和挑战"},
    {"purpose": "解决方案", "content": "概述方法和技术路线"},
    {"purpose": "贡献总结", "content": "明确列出贡献点"}
  ],
  "contributions": ["贡献1", "贡献2"]
}
```

### review_result.json
```json
{
  "source_file": "draft.md",
  "generated_at": "2026-06-09T12:00:00",
  "issues": [
    {
      "severity": "MAJOR",
      "category": "logic",
      "location": "Section 3.2",
      "description": "论证逻辑不完整",
      "suggestion": "补充实验支持"
    },
    {
      "severity": "MINOR",
      "category": "grammar",
      "location": "Abstract",
      "description": "冠词使用错误",
      "suggestion": "将 'a' 改为 'the'"
    }
  ],
  "summary": {
    "critical": 0,
    "major": 1,
    "minor": 1
  },
  "verdict": "Needs Revision"
}
```
