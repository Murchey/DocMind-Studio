# PhD Research Agent - 精简版

科研辅助 Agent，提供 Idea 评估、Introduction 草稿、论文审阅等核心能力。

## 目录结构

```
phd-research-agent/
├── AGENT.md                    # Agent 配置文件
├── README.md                   # 本文件
├── SKILLS/                     # 技能目录
│   ├── idea-evaluator/         # Idea 评估技能
│   │   └── SKILL.md
│   ├── intro-drafter/          # Introduction 起草技能
│   │   └── SKILL.md
│   └── pre-submission-reviewer/ # 论文审阅技能
│       └── SKILL.md
└── workspace/                  # 工作区
    ├── input/                  # 输入目录（只读）
    └── summary/                # 输出目录
```

## 快速开始

### 1. 评估研究想法

将研究想法写入 `workspace/input/idea.md`，然后执行：

```python
# 读取 AGENT.md 了解执行流程
# 读取 SKILLS/idea-evaluator/SKILL.md 了解评估方法
# 执行评估并输出结果到 workspace/summary/
```

### 2. 起草 Introduction

将研究信息写入 `workspace/input/research_info.md`，然后执行：

```python
# 读取 SKILLS/intro-drafter/SKILL.md 了解起草方法
# 执行起草并输出结果到 workspace/summary/
```

### 3. 审阅论文

将论文草稿写入 `workspace/input/draft.md`，然后执行：

```python
# 读取 SKILLS/pre-submission-reviewer/SKILL.md 了解审阅方法
# 执行审阅并输出结果到 workspace/summary/
```

## 输出格式

所有输出均包含：
- `manifest.json`：处理清单
- `<task>_result.json`：结构化结果
- `<task>_result.md`：可读报告

## 集成指南

### 作为独立 Agent 使用

1. 将 `phd-research-agent` 目录复制到目标项目
2. 按照 AGENT.md 中的流程执行
3. 读取 `workspace/summary/` 获取结果

### 集成到多 Agent 系统

1. 将 `phd-research-agent` 目录复制到 `ComponentAgents/` 目录
2. 在调度器中添加对本 Agent 的描述
3. 按照规范调用本 Agent

## 参考仓库
原仓库内容：https://github.com/HKUSTDial/Supervisor-Skills/fork

原README标注：本项目采用 [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/) 协议开源。欢迎非商业用途的分享与改编，但请注明出处。

