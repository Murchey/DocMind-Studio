---
name: pre-submission-reviewer
description: 论文提交前审阅，检查逻辑、语法、格式
tools: [markdown]
---

# Pre-Submission Reviewer

## 功能说明

对论文进行全面审阅，检查逻辑、语法、格式等问题，给出修改建议。

## 输入/输出

**输入**：
- `workspace/input/draft.md`：论文草稿

**输出**：
- `workspace/summary/review_result.json`：结构化审阅结果
- `workspace/summary/review_result.md`：可读审阅报告

## 调用方式

```python
def review_paper(draft_text: str, source_file: str = "draft.md") -> dict:
    """
    审阅论文草稿
    
    Args:
        draft_text: 论文草稿文本
        source_file: 原始文件名（用于追溯）
    
    Returns:
        {
            "source_file": "draft.md",
            "generated_at": "2026-06-09T12:00:00",
            "issues": [
                {
                    "severity": "CRITICAL | MAJOR | MINOR",
                    "category": "logic | grammar | format | figure",
                    "location": "问题位置",
                    "description": "问题描述",
                    "suggestion": "修改建议"
                }
            ],
            "summary": {
                "critical": 0,
                "major": 0,
                "minor": 0
            },
            "verdict": "Ready | Needs Revision | Not Ready"
        }
    """
```

## 核心流程

### Step 1: 宏观逻辑检查
- 论文结构是否完整
- 逻辑链条是否连贯
- 贡献是否明确

### Step 2: 写作细节检查
- 段落是否有主题句
- 引用格式是否统一
- 术语使用是否一致

### Step 3: 英文语法检查
- 冠词使用
- 主谓一致
- 时态一致性
- which/that 区分

### Step 4: LaTeX 格式检查
- 数学公式格式
- 图表引用
- 参考文献格式

### Step 5: 图表质量检查
- 图表是否清晰
- 标签是否完整
- 字体大小是否合适

## 问题严重性分类

| 级别 | 说明 | 处理方式 |
|------|------|----------|
| CRITICAL | 致命问题，必须修复 | 阻止提交 |
| MAJOR | 严重问题，强烈建议修复 | 强烈建议修复 |
| MINOR | 轻微问题，建议修复 | 可选修复 |

## 输出示例

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

## 错误处理

- 输入文件不存在 → 返回空结果
- 审阅过程出错 → 返回错误信息
