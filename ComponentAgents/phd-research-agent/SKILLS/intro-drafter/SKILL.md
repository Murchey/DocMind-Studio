---
name: intro-drafter
description: 起草论文 Introduction 的六段式大纲
tools: [markdown]
---

# Introduction Drafter

## 功能说明

根据研究信息，生成六段式 Introduction 大纲，确保逻辑连贯、贡献清晰。

## 输入/输出

**输入**：
- `workspace/input/research_info.md`：研究信息

**输出**：
- `workspace/summary/intro_outline.json`：结构化大纲
- `workspace/summary/intro_outline.md`：可读大纲

## 调用方式

```python
def draft_intro(research_info: dict) -> dict:
    """
    起草 Introduction 大纲
    
    Args:
        research_info: {
            "area": "研究领域",
            "limitations": "现有工作局限性",
            "key_idea": "核心想法",
            "challenges": ["挑战1", "挑战2"],
            "solution": "解决方案概述"
        }
    
    Returns:
        {
            "paragraphs": [
                {"purpose": "段落目的", "content": "要点"},
                ...
            ],
            "contributions": ["贡献1", "贡献2"]
        }
    """
```

## 核心流程

### Step 1: 信息提取
从输入中提取：
- 研究领域
- 现有工作局限性
- 核心想法
- 关键挑战
- 解决方案概述

### Step 2: 六段式结构

| 段落 | 目的 | 内容要点 |
|------|------|----------|
| P1 | 背景介绍 | 领域重要性、研究对象 |
| P2 | 现有工作 | 现有方法及其局限性 |
| P3 | 问题本质 | 核心问题、研究目标 |
| P4 | 关键挑战 | 技术难点、挑战列表 |
| P5 | 解决方案 | 方法概述、技术路线 |
| P6 | 贡献总结 | 明确列出贡献点 |

### Step 3: 贡献对齐
确保每个贡献对应一个挑战，每个贡献有对应的章节。

## 输出示例

```json
{
  "paragraphs": [
    {
      "purpose": "背景介绍",
      "content": "介绍研究领域的重要性和研究对象"
    },
    {
      "purpose": "现有工作",
      "content": "总结现有方法及其局限性"
    },
    {
      "purpose": "问题本质",
      "content": "明确核心问题和研究目标"
    },
    {
      "purpose": "关键挑战",
      "content": "列出技术难点和挑战"
    },
    {
      "purpose": "解决方案",
      "content": "概述方法和技术路线"
    },
    {
      "purpose": "贡献总结",
      "content": "明确列出贡献点"
    }
  ],
  "contributions": ["贡献1", "贡献2"]
}
```

## 错误处理

- 输入信息不完整 → 返回提示，要求补充
- 无法提取关键信息 → 返回错误
