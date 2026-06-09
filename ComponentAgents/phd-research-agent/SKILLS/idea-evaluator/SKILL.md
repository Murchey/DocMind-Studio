---
name: idea-evaluator
description: 评估研究想法的可行性、创新性和价值
tools: [markdown]
---

# Idea Evaluator

## 功能说明

评估研究想法，从五个维度打分，识别致命缺陷，给出接受/修改/拒绝建议。

## 输入/输出

**输入**：
- `workspace/input/idea.md`：研究想法描述

**输出**：
- `workspace/summary/idea_result.json`：结构化评估结果
- `workspace/summary/idea_result.md`：可读评估报告

## 调用方式

```python
def evaluate_idea(idea_text: str, source_file: str = "idea.md") -> dict:
    """
    评估研究想法
    
    Args:
        idea_text: 研究想法描述文本
        source_file: 原始文件名（用于追溯）
    
    Returns:
        {
            "source_file": "idea.md",
            "generated_at": "2026-06-09T12:00:00",
            "verdict": "Strong Accept | Accept with Revisions | Reject and Pivot",
            "scores": {
                "higher": 1-5,  # 更高：提升性能/效果
                "faster": 1-5,  # 更快：提升效率/速度
                "stronger": 1-5, # 更强：增强鲁棒性/泛化
                "cheaper": 1-5,  # 更省：降低成本/资源
                "broader": 1-5   # 更广：扩展应用场景
            },
            "fatal_flaws": ["缺陷描述"],
            "suggestions": ["改进建议"]
        }
    """
```

## 核心流程

### Step 1: 致命缺陷检查
检查以下致命缺陷：
1. 问题定义模糊
2. 创新性不足
3. 技术路线不可行
4. 与现有工作重复

### Step 2: 五维评分
| 维度 | 评分标准 |
|------|----------|
| 更高 | 是否能显著提升性能/效果 |
| 更快 | 是否能提升效率/速度 |
| 更强 | 是否能增强鲁棒性/泛化能力 |
| 更省 | 是否能降低成本/资源消耗 |
| 更广 | 是否能扩展应用场景 |

### Step 3: 给出建议
- **Strong Accept**：无致命缺陷，总分 ≥ 20
- **Accept with Revisions**：无致命缺陷，总分 < 20
- **Reject and Pivot**：存在致命缺陷

## 错误处理

- 输入文件不存在 → 返回空结果
- 评估过程出错 → 返回错误信息
