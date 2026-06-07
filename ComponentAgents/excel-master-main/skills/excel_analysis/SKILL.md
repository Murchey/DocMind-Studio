---
name: "excel_analysis"
description: "增强数据分析技能，支持按用户业务需求进行特定方向和区域的数据比对分析，涵盖公司表格和学术内容表格，支持附加 MD 文档作为参考，AI 进行数据分析总结并输出 JSON 结果"
---

# Excel Analysis Skill (增强数据分析技能)

## 核心目标

提供一个增强的数据分析能力，支持按照用户的输入和业务需求，完成特定方向和区域的数据比对分析。内容涵盖**公司表格**和**学术内容表格**，允许用户附加 **MD 文档作为参考内容**，由 AI 进行数据分析总结，最后在工作区输出 JSON 文件保存分析结果。

## 触发时机

- 用户需要对 Excel 数据进行**业务方向分析**（如财务分析、销售趋势、学术成绩分析等）
- 用户需要**附加参考文档**（MD 格式）来指导数据分析
- 用户需要 AI 进行**智能数据总结**并输出结构化 JSON 结果
- 用户需要对**公司表格**或**学术内容表格**进行深度分析
- 用户需要按照**特定区域或业务领域**进行数据比对

## 核心功能

### 1. 业务方向分析

支持多种业务场景的数据分析：

**公司表格分析**：
- 财务报表分析（资产负债表、利润表、现金流量表）
- 销售数据分析（销售额趋势、客户分析、产品分析）
- 人力资源分析（员工绩效、薪酬分析、人员流动）
- 项目管理分析（进度跟踪、成本控制、资源分配）

**学术内容表格分析**：
- 学生成绩分析（成绩分布、趋势分析、学科对比）
- 教学质量评估（教师评价、课程效果）
- 科研数据分析（实验数据、调查问卷、统计分析）
- 学术论文数据（引用分析、影响因子）

### 2. 参考文档支持

- 支持附加 **Markdown (.md)** 文档作为分析参考
- 参考文档可以包含：
  - 业务背景说明
  - 数据字典定义
  - 分析指标说明
  - 历史分析报告
  - 行业标准或阈值

### 3. AI 智能分析总结

- 自动识别数据特征和业务含义
- 基于参考文档进行上下文理解
- 生成结构化的分析总结
- 提供数据洞察和建议

### 4. JSON 结果输出

分析结果以 JSON 格式保存到工作区，包含：
- 分析元数据（时间、参数、文件信息）
- 数据摘要统计
- 分析结论和洞察
- 参考文档引用
- 可视化建议

## 工具调用方式

- 脚本路径：`skills/excel_analysis/scripts/analysis.py`
- 调用命令：`python skills/excel_analysis/scripts/analysis.py <数据文件或目录> [选项]`

## 参数说明

| 参数 | 必填 | 说明 |
|------|------|------|
| `数据文件或目录` | 是 | Excel/CSV 文件路径或包含这些文件的目录路径 |
| `--reference` | 否 | 附加的参考 MD 文档路径（可多个） |
| `--direction` | 否 | 分析方向：`company`（公司）、`academic`（学术）、`general`（通用，默认） |
| `--area` | 否 | 分析区域/领域：如 `finance`、`sales`、`grades`、`research` 等 |
| `--output` | 否 | JSON 输出路径，默认保存到工作区 `excel_output/analysis_result.json` |
| `--max-rows` | 否 | 最大加载行数，用于大文件优化 |

## 目录扫描支持

当传入目录路径时，脚本会自动递归扫描所有子目录中的 `.xlsx`、`.xls` 和 `.csv` 文件，并按子目录分组进行分析。

## 分析方向详解

### 公司表格分析 (company)

**财务分析 (finance)**：
- 资产负债表结构分析
- 利润表趋势分析
- 现金流量分析
- 财务比率计算（流动比率、速动比率、资产负债率等）

**销售分析 (sales)**：
- 销售额趋势分析
- 客户贡献度分析
- 产品销售排名
- 区域销售对比

**人力资源分析 (hr)**：
- 员工绩效评估
- 薪酬结构分析
- 人员流动率分析
- 部门效率对比

### 学术内容表格分析 (academic)

**成绩分析 (grades)**：
- 成绩分布统计（平均分、中位数、标准差）
- 学科成绩对比
- 班级/年级成绩趋势
- 学生个人成绩分析

**教学质量评估 (teaching)**：
- 教师评价分析
- 课程效果评估
- 教学资源使用分析

**科研数据分析 (research)**：
- 实验数据统计分析
- 调查问卷结果分析
- 数据相关性分析

## 参考文档格式

参考文档应为 Markdown 格式，建议包含以下内容：

```markdown
# 分析背景

## 业务说明
描述数据的业务背景和分析目的

## 数据字典
| 列名 | 数据类型 | 说明 |
|------|----------|------|
| 日期 | 日期 | 数据记录日期 |
| 销售额 | 数值 | 当日销售额（元） |

## 分析指标
- 关键指标1：计算方法和阈值
- 关键指标2：计算方法和阈值

## 历史参考
历史分析结果或行业标准
```

## 脚本输出格式

脚本将输出 JSON 格式的分析结果：

```json
{
  "status": "success",
  "analysis_time": "2026-06-07 10:30:00",
  "input_files": ["file1.xlsx", "file2.xlsx"],
  "direction": "company",
  "area": "finance",
  "reference_docs": ["background.md"],
  "summary": {
    "total_files": 2,
    "total_rows": 1000,
    "total_columns": 15
  },
  "data_profile": {
    "file1.xlsx": {
      "columns": ["日期", "销售额", "成本", "利润"],
      "row_count": 500,
      "data_quality": {
        "null_percentage": 2.5,
        "duplicate_rows": 0
      }
    }
  },
  "analysis_results": {
    "key_metrics": {
      "total_sales": 1500000,
      "average_daily_sales": 5000,
      "profit_margin": 0.25
    },
    "trends": {
      "sales_trend": "increasing",
      "growth_rate": 0.15
    },
    "insights": [
      "销售额呈现稳定增长趋势",
      "利润率保持在健康水平",
      "建议关注成本控制以提高利润"
    ]
  },
  "reference_summary": {
    "background.md": {
      "sections_found": ["业务说明", "数据字典", "分析指标"],
      "key_terms": ["销售额", "利润率", "成本控制"]
    }
  },
  "recommendations": [
    "建议继续监控销售趋势",
    "关注成本结构优化",
    "定期进行财务比率分析"
  ]
}
```

## 使用示例

### 1. 公司财务分析

```powershell
# 分析财务报表，附加业务背景文档
python skills/excel_analysis/scripts/analysis.py "D:\workspace\project\temp\financial_data.xlsx" --direction company --area finance --reference "D:\workspace\project\temp\business_background.md"
```

### 2. 学生成绩分析

```powershell
# 分析学生成绩，附加课程说明
python skills/excel_analysis/scripts/analysis.py "D:\workspace\project\temp\grades" --direction academic --area grades --reference "D:\workspace\project\temp\course_description.md"
```

### 3. 销售数据分析

```powershell
# 分析销售数据目录
python skills/excel_analysis/scripts/analysis.py "D:\workspace\project\temp\sales_data" --direction company --area sales --output "D:\workspace\project\excel_output\sales_analysis.json"
```

### 4. 通用分析（无参考文档）

```powershell
# 通用数据分析
python skills/excel_analysis/scripts/analysis.py "D:\workspace\project\temp\data.xlsx" --direction general
```

## 工作流整合

### 1. 在定制化需求中的使用

```
1. 用户要求分析 Excel 数据
2. Agent 创建工作区并读取文件
3. Agent 调用 data_profile 进行数据探查
4. Agent 调用 excel_preview confirm 启动 Web 服务确认需求
5. 用户确认分析方向、区域和参考文档
6. Agent 调用 excel_analysis 进行深度分析
7. Agent 生成分析报告和 JSON 结果
8. 保存结果到工作区
```

### 2. 独立分析模式

```
1. 用户提供数据文件和参考文档
2. Agent 创建工作区
3. Agent 调用 excel_analysis 进行分析
4. 输出 JSON 分析结果
5. Agent 向用户展示分析摘要
```

## Agent 行为约束

1. **分析前必须确认方向**：询问用户分析方向（公司/学术）和具体领域
2. **参考文档可选**：如果用户提供了 MD 文档，必须附加到分析中
3. **结果必须保存**：分析结果必须保存为 JSON 文件到工作区
4. **摘要必须展示**：向用户展示分析摘要和关键洞察
5. **大数据优化**：对于大文件，使用 `--max-rows` 参数限制加载行数

## 注意事项

1. 本技能支持 `.xlsx`、`.xls` 和 `.csv` 文件
2. 参考文档必须为 `.md` 格式
3. 分析结果默认保存到工作区 `excel_output/analysis_result.json`
4. 对于超大文件，建议使用 `--max-rows` 参数
5. AI 分析基于数据特征和参考文档，不进行实时计算
6. 分析结果仅供参考，重要决策需人工复核

## 常见问题与解决方案

### 1. 参考文档格式不支持

**问题描述**：用户提供的参考文档不是 MD 格式。

**解决方案**：
- 提示用户将文档转换为 Markdown 格式
- 或者让 Agent 帮助提取文档内容并转换为 MD 格式

### 2. 分析方向不明确

**问题描述**：用户未指定分析方向或领域。

**解决方案**：
- Agent 通过数据探查结果推测可能的分析方向
- 询问用户确认分析方向和具体需求
- 提供默认的通用分析模式

### 3. 数据量过大

**问题描述**：数据文件过大导致分析缓慢。

**解决方案**：
- 使用 `--max-rows` 参数限制加载行数
- 建议用户先进行数据筛选
- 分批处理大型数据集

### 4. 多文件分析

**问题描述**：需要分析多个相关文件。

**解决方案**：
- 传入目录路径，脚本自动递归扫描
- 确保所有文件结构相似或有关联性
- 参考文档中说明文件间的关系
