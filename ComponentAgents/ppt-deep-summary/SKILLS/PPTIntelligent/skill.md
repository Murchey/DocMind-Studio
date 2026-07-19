| name | ppt_intelligent |
| ---- | --------------- |
| description | 基于 AI 模型的 PPT 深度智能分析。无需外部 API 配置，直接利用当前模型进行语义理解、逻辑推理和智能总结。 |

# PPTIntelligent Skill（AI 原生）

## 核心目标

直接利用当前 AI 模型对 PPT 内容进行深度智能分析，包括语义理解、逻辑推理、因果分析和高质量总结。**无需配置外部 API，模型即分析引擎。**

## 触发时机

- PPTParser 解析完成后
- PPTAnalyst 内容分析完成后
- 用户要求"深度分析"、"智能分析"、"语义分析"、"逻辑推理"

## 调用方式

本 Skill 由 AI 助手直接执行，不依赖 Python 脚本调用外部 API。

AI 助手读取 `WorkSpace/parsed.json`（PPTParser 输出），然后自主完成以下分析任务：

1. **语义分析**：理解每页内容的含义，识别核心概念、主要论点、隐含假设
2. **逻辑分析**：分析因果关系，识别推理链条，发现隐含联系
3. **智能总结**：生成高质量总结，提炼关键洞察，识别创新亮点和潜在问题
4. **输出**：将分析结果写入 `WorkSpace/intelligent.json`

脚本辅助（可选）：
```bash
# 如需生成纯文本上下文供 AI 参考：
python SKILLS/PPTIntelligent/scripts/ppt_intelligent.py WorkSpace/parsed.json WorkSpace/context.txt
```

## 分析任务详细说明

### 任务一：语义分析（semantic_analysis）

读取 `WorkSpace/parsed.json` 中所有幻灯片的文本内容，进行深度语义理解：

**核心概念（core_concepts）**：
- 从全文中识别 5-15 个核心概念和关键术语
- 概念应覆盖主题、技术、用户、市场等维度
- 每个概念应是高度概括的词语或短语

**主要论点（key_arguments）**：
- 识别 PPT 中的核心论点和价值主张
- 每个论点必须包含：
  - `argument`：论点内容（简洁清晰）
  - `evidence`：支撑证据（引用原文）
  - `source_slide`：来源页码
  - `strength`：论证强度（strong/medium/weak）

**隐含假设（implicit_assumptions）**：
- 识别 PPT 未明确说明但隐含的前提条件
- 通常涉及市场需求、用户行为、技术可行性、政策环境等方面

### 任务二：逻辑分析（logical_analysis）

分析 PPT 内容的逻辑结构和推理关系：

**推理链条（reasoning_chains）**：
- 识别 PPT 中的完整推理过程
- 每条链条包含：
  - `premise`：前提/出发点
  - `conclusion`：结论/目标
  - `logical_validity`：逻辑有效性（valid/questionable/invalid）
  - `source_slides`：支撑的页码列表

**因果关系（cause_effect_relationships）**：
- 分析内容中的因果逻辑
- 每条关系包含：
  - `cause`：原因
  - `effect`：结果
  - `confidence`：置信度（high/medium/low）

**隐含联系（hidden_connections）**：
- 发现不同部分之间的深层关联
- 识别跨页面的主题呼应和逻辑闭环

### 任务三：智能总结（intelligent_summary）

基于前两项分析结果，生成高质量总结：

**一句话总结（one_sentence_summary）**：
- 用一句话精准概括整个 PPT 的核心内容
- 应包含项目/产品名称、定位、核心价值

**关键洞察（key_insights）**：
- 提炼 3-7 个最重要的洞察
- 每个洞察包含：
  - `insight`：洞察内容
  - `significance`：重要性（high/medium/low）
  - `source_slide`：来源页码

**创新亮点（innovation_highlights）**：
- 识别 3-7 个创新点或差异化优势
- 用简洁的短语描述

**潜在问题（potential_issues）**：
- 发现 2-5 个潜在风险或不足
- 基于内容逻辑和行业常识判断

**整体评价（overall_assessment）**：
- 从结构完整性、论证质量、创新性、可行性四个维度进行评价
- 给出优势和改进建议

## 输出格式

将分析结果写入 `WorkSpace/intelligent.json`，JSON 结构如下：

```json
{
  "semantic_analysis": {
    "core_concepts": ["概念1", "概念2"],
    "key_arguments": [
      {
        "argument": "论点",
        "evidence": "证据",
        "source_slide": 7,
        "strength": "strong"
      }
    ],
    "implicit_assumptions": ["假设1", "假设2"]
  },
  "logical_analysis": {
    "reasoning_chains": [
      {
        "premise": "前提",
        "conclusion": "结论",
        "logical_validity": "valid",
        "source_slides": [3, 4]
      }
    ],
    "cause_effect_relationships": [
      {
        "cause": "原因",
        "effect": "结果",
        "confidence": "high"
      }
    ],
    "hidden_connections": ["联系1", "联系2"]
  },
  "intelligent_summary": {
    "one_sentence_summary": "一句话总结",
    "key_insights": [
      {
        "insight": "洞察内容",
        "significance": "high",
        "source_slide": 3
      }
    ],
    "innovation_highlights": ["亮点1", "亮点2"],
    "potential_issues": ["问题1", "问题2"],
    "overall_assessment": "整体评价"
  },
  "analysis_timestamp": "ISO时间戳",
  "analyzer": "AI-native-model",
  "warnings": []
}
```

## 执行步骤

1. 读取 `WorkSpace/parsed.json`，理解全部幻灯片内容
2. 执行语义分析，识别概念、论点和假设
3. 执行逻辑分析，识别推理链、因果关系和隐含联系
4. 执行智能总结，生成总结、洞察、亮点和评价
5. 将完整结果写入 `WorkSpace/intelligent.json`
6. 如果 `WorkSpace/intelligent.json` 已存在，覆盖更新

## Agent 约束

- 分析必须基于 PPT 实际内容，严禁编造
- 所有论点和洞察必须标注来源页码
- 不确定的推断标注为 `medium` 或 `low` 置信度
- 一句话总结必须精准概括核心内容
- 整体评价应客观平衡，既指出优势也指出不足
- 分析结果写入 JSON 文件后，向用户展示关键发现摘要

## 注意事项

- 依赖 PPTParser 的输出（parsed.json），不能直接处理 .pptx 文件
- 分析质量取决于 AI 模型的理解能力
- 如果 parsed.json 不存在，提示用户先执行 PPTParser
- 内容过多时（>50页），优先分析前30页和末尾5页
