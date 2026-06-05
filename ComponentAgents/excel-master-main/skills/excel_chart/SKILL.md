---
name: "excel_chart"
description: "基于数据探查结果生成数据图表，支持柱状图、折线图、饼图等多种图表类型。当用户需要可视化数据或生成分析报告时调用。"
---

# Excel Chart Skill (数据图表生成技能)

## 核心目标

基于 `data_profile` 技能处理后的数据，生成可视化图表，帮助用户更直观地理解数据特征和趋势。

## 触发时机

- 用户要求生成数据图表或可视化报告
- 用户需要分析数据趋势、分布或对比
- 数据探查完成后，需要将结果可视化展示
- 用户明确要求生成柱状图、折线图、饼图等图表

## 工具调用方式

- 脚本路径：`skills/excel_chart/scripts/generate_chart.py`
- 调用命令：`python skills/excel_chart/scripts/generate_chart.py <数据文件路径> [图表类型] [数据范围] [输出目录] [--max-rows 行数]`

## 参数说明

| 参数 | 必填 | 说明 |
|------|------|------|
| `数据文件路径` | 是 | 数据文件（Excel 或 CSV）的绝对或相对路径 |
| `图表类型` | 否 | 图表类型，可选值：`bar`（柱状图）、`line`（折线图）、`pie`（饼图）、`scatter`（散点图）。默认为 `bar` |
| `数据范围` | 否 | JSON 格式的数据范围描述，包含列名、行范围、筛选条件等 |
| `输出目录` | 否 | 图表保存目录。如不指定，默认保存到工作区的 `excel_output` 目录 |
| `--max-rows` | 否 | 最大加载行数，用于大文件优化 |

### 数据范围参数格式

`数据范围` 参数为 JSON 格式字符串，包含以下字段：

```json
{
  "columns": ["列名1", "列名2"],  // 要展示的列，为空则展示所有列
  "rows": {"start": 0, "end": 100},  // 行范围，可选
  "filter": {"列名": "条件值"}  // 筛选条件，可选
}
```

**示例**：
- 展示所有行的数学和物理成绩：`{"columns": ["数学", "物理"]}`
- 展示前10行数据：`{"rows": {"start": 0, "end": 10}}`
- 筛选一班的数据：`{"filter": {"班级": "一班"}}`
- 组合条件：`{"columns": ["姓名", "数学"], "filter": {"班级": "一班"}, "rows": {"start": 0, "end": 20}}`

## 支持的图表类型

### 1. 柱状图 (bar)
- **适用场景**：比较不同类别的数值大小
- **典型应用**：各班级成绩对比、不同科目平均分比较
- **示例**：比较一班、二班、三班的数学平均分

### 2. 折线图 (line)
- **适用场景**：展示数据随时间或顺序的变化趋势
- **典型应用**：学生成绩变化趋势、时间序列数据
- **示例**：展示某学生历次考试成绩变化

### 3. 饼图 (pie)
- **适用场景**：展示各部分占整体的比例关系
- **典型应用**：成绩等级分布、性别比例
- **示例**：展示优秀、良好、及格、不及格的学生比例

### 4. 散点图 (scatter)
- **适用场景**：展示两个变量之间的关系
- **典型应用**：相关性分析、分布特征
- **示例**：展示数学成绩与物理成绩的关系

## 脚本输出格式

脚本将输出一段 JSON 格式的字符串，包含以下信息：

- `status`：执行状态（success/error）
- `chart_type`：生成的图表类型
- `output_file`：图表文件保存路径
- `message`：执行结果描述

### 成功输出示例

```json
{
  "status": "success",
  "chart_type": "bar",
  "output_file": "D:\\workspace\\project\\excel_output\\chart_班级数学平均分对比.png",
  "message": "图表生成成功"
}
```

### 错误输出示例

```json
{
  "status": "error",
  "chart_type": "bar",
  "output_file": "",
  "message": "文件不存在: D:\\data\\nonexistent.xlsx"
}
```

## Agent 行为约束

1. 在生成图表前，**必须**先调用 `data_profile` 技能获取数据特征
2. **必须询问用户**以下信息：
   - **图表类型**：向用户展示支持的图表类型（柱状图、折线图、饼图、散点图），让用户选择
   - **数据范围**：要求用户描述需要展示的数据范围（如：哪些列、哪些行、是否需要筛选条件）
3. 根据用户选择的图表类型和数据范围生成图表
4. 如果用户未指定，根据数据特征推荐合适的图表类型，并说明推荐理由
5. 图表标题和标签应使用中文，便于用户理解
6. 生成图表后，询问用户是否满意，是否需要调整

## 使用示例

### 基本调用（默认柱状图）

```powershell
python skills/excel_chart/scripts/generate_chart.py "D:\workspace\project\temp\学生成绩.xlsx"
```

### 指定图表类型

```powershell
python skills/excel_chart/scripts/generate_chart.py "D:\workspace\project\temp\学生成绩.xlsx" "pie"
```

### 指定数据范围

```powershell
# 展示数学和物理成绩
python skills/excel_chart/scripts/generate_chart.py "D:\workspace\project\temp\学生成绩.xlsx" "bar" "{\"columns\": [\"数学\", \"物理\"]}"

# 筛选一班的数据
python skills/excel_chart/scripts/generate_chart.py "D:\workspace\project\temp\学生成绩.xlsx" "bar" "{\"filter\": {\"班级\": \"一班\"}}"

# 展示前10行数据
python skills/excel_chart/scripts/generate_chart.py "D:\workspace\project\temp\学生成绩.xlsx" "bar" "{\"rows\": {\"start\": 0, \"end\": 10}}"
```

### 指定输出目录

```powershell
python skills/excel_chart/scripts/generate_chart.py "D:\workspace\project\temp\学生成绩.xlsx" "bar" "{}" "D:\workspace\project\excel_output"
```

## 工作流整合

### 1. 与 data_profile 技能配合

```
数据文件 → data_profile 探查 → 分析数据特征 → excel_chart 生成图表
```

### 2. 在定制化需求中的使用

在数据探查完成后，如果用户需要可视化展示，调用此技能生成图表：

```
1. 调用 data_profile 获取数据特征
2. 向用户展示数据特征（列名、数据类型、样例数据）
3. 询问用户需要生成什么类型的图表
4. 询问用户需要展示的数据范围（哪些列、哪些行、筛选条件）
5. 根据用户选择调用 excel_chart 生成图表
6. 将图表保存到工作区 excel_output 目录
7. 向用户展示图表并询问反馈
```

### 3. 在通用化需求中的使用

在批量处理完成后，生成汇总图表：

```
1. 批量处理多个表格
2. 汇总处理结果
3. 调用 excel_chart 生成汇总图表
4. 将图表保存到工作区 excel_output 目录
```

## 图表生成规则

### 1. 数据选择规则
- 自动识别数值列（如成绩、年龄）和分类列（如班级、性别）
- 对于数值列，计算统计指标（平均值、总和、最大值、最小值）
- 对于分类列，统计各类别的数量或比例

### 2. 图表美化规则
- 使用清晰的中文标题和标签
- 选择合适的颜色方案
- 添加图例说明
- 设置合适的坐标轴范围

### 3. 输出格式规则
- 图表保存为 PNG 格式，分辨率 300 DPI
- 文件名包含图表类型和描述信息
- 保存到指定目录或默认的 excel_output 目录

## 注意事项

1. 本技能依赖 `matplotlib` 和 `pandas` 库，确保已安装
2. 图表生成可能需要较长时间，特别是大数据集
3. 如果数据文件格式不正确或数据不完整，会返回错误信息
4. 生成的图表文件会覆盖同名文件，请注意文件命名
5. 对于复杂的数据分析需求，可能需要生成多个图表

## 依赖库

- `matplotlib`：用于生成图表
- `pandas`：用于数据处理
- `openpyxl`：用于读取 Excel 文件

确保已安装依赖：

```powershell
pip install matplotlib pandas openpyxl
```