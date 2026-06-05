---
name: "excel_preview"
description: "Excel 文件可视化预览与操作技能，提供网页界面让用户可视化地进行需求确认、文件比对和合并操作。遵循页面操作可视化原则，减少 Agent Token 消耗。"
---

# Excel Preview Skill (可视化预览操作技能)

## 核心目标

提供一个本地 Web 服务，让用户通过可视化网页界面进行 Excel 文件的**需求确认**、比对和合并操作，**减少 Agent Token 消耗**，提升用户体验。

## 触发时机

- **任何表格操作前（必须）**：在数据探查完成后、生成脚本之前，必须打开 WEB 页面让用户确认需求
- 用户需要比对两个或多个 Excel 文件的差异
- 用户需要合并多个 Excel 文件
- 用户希望可视化地选择比对列、筛选条件或合并规则
- 用户对数据操作规则不确定，需要交互式界面
- 处理完成后，根据需求展示结果预览

## 设计原则

1. **需求确认前置原则**：在生成脚本之前，先通过 WEB 页面让用户确认处理需求
2. **页面操作可视化原则**：所有复杂操作通过网页界面完成，用户可以鼠标点击选择
3. **Agent 最小 Token 原则**：Agent 只需调用启动命令，具体操作由用户在网页完成
4. **交互友好原则**：提供直观的界面，减少用户学习成本

## 工具调用方式

- 脚本路径：`skills/excel_preview/scripts/preview_server.py`
- 调用命令：`python skills/excel_preview/scripts/preview_server.py <操作类型> <文件或目录路径1> [文件或目录路径2 ...] [--port 端口号] [--max-rows 行数]`

## 参数说明

| 参数 | 必填 | 说明 |
|------|------|------|
| `操作类型` | 是 | `confirm`（需求确认）、`compare`（比对）、`merge`（合并）、`summary`（摘要）或 `result`（结果预览） |
| `文件或目录路径1` | 是 | Excel 文件路径或包含 Excel 文件的目录路径（自动递归扫描子目录） |
| `文件或目录路径2` | 否 | 第二个文件/目录路径（比对时必填） |
| `--port` | 否 | Web 服务端口号，默认 5000 |
| `--max-rows` | 否 | 最大加载行数，用于大文件优化 |

## 目录扫描支持

当传入目录路径时，脚本会自动递归扫描所有子目录中的 `.xlsx`、`.xls` 和 `.csv` 文件，并按子目录分组展示。

## 表头自动检测

脚本会自动检测 Excel 文件的表头行位置，解决以下常见问题：
- 文件开头有标题行（如"某某学校2025年秋季学期..."）
- 文件开头有多行空行或合并单元格
- 不同文件的表头行位置不一致

检测逻辑：
1. 逐行扫描前10行数据
2. 找到第一个包含3个以上非空值的行
3. 如果该行的"Unnamed"列少于50%，则认为是表头行
4. 使用检测到的表头行作为列名加载数据

## 同名文件比对规则

**重要**：比对模式要求两个目录中存在**同名文件**（或语义相同的文件）。

- 系统会自动配对两个目录中文件名完全相同的文件
- 配对后的文件使用**相同的比对规则**（列选择、匹配模式等）
- 用户在网页界面选择的规则将应用于**所有配对的同名文件**
- 如果文件名不同，系统会提示用户确保文件命名一致

**示例**：
```
左侧目录/标准收取账目/
├── 2.1.xlsx
├── 2.2.xlsx
└── 2.3.xlsx

右侧目录/待比对账目/
├── 2.1.xlsx
├── 2.2.xlsx
└── 2.3.xlsx

→ 自动配对：2.1.xlsx ↔ 2.1.xlsx, 2.2.xlsx ↔ 2.2.xlsx, 2.3.xlsx ↔ 2.3.xlsx
```

## 比对配置结构

用户在网页界面需要配置以下内容：

| 配置项 | 必填 | 说明 |
|--------|------|------|
| **主键列** | 是 | 选择一个在左右表中都存在的列作为匹配依据（如"姓名"），用于唯一标识记录 |
| **副键列** | 否 | 在主键相同的情况下，进一步筛选匹配条件（如"班级"），可选多个或0个 |
| **左侧值列** | 是* | 选择左侧表中要比对的数值列（如"金额（元）"） |
| **右侧值列** | 是* | 选择右侧表中要比对的数值列（如"已线上缴费金额"） |

*注：左侧值列和右侧值列至少选择一个

**配置示例**：
```json
{
  "primary_key": "姓名",
  "secondary_keys": ["班级"],
  "left_value_columns": ["金额（元）"],
  "right_value_columns": ["已线上缴费金额"]
}
```

**比对逻辑**：
1. 使用主键列（+副键列）匹配左右表中的记录
2. 对匹配的记录，比较左侧值列和右侧值列的值
3. 输出差异记录（包括：仅在左侧、仅在右侧、值不一致）

## 支持的操作模式

### 0. 需求确认模式 (confirm) - 必须

**功能**：
- 在数据探查完成后、生成脚本之前，打开 WEB 页面让用户确认处理需求
- 展示数据预览和结构信息
- 让用户选择需要处理的列
- 让用户指定处理方式和规则
- 让用户填写特殊要求和备注
- 输出用户确认的需求配置，供 Agent 生成脚本使用

**使用场景**：
- **任何表格操作前必须使用**：确保生成的脚本完全符合用户需求
- 定制化需求：精细分析、文本处理、复杂整合
- 通用化需求：批量处理、简单比对

**输出格式**：
```json
{
  "status": "confirmed",
  "operation": "confirm",
  "config": {
    "selected_columns": ["姓名", "金额", "班级"],
    "processing_rules": {
      "type": "compare",
      "match_type": "exact",
      "ignore_null": true
    },
    "notes": "用户填写的备注信息"
  },
  "message": "需求已确认，配置已保存"
}
```

### 1. 文件比对模式 (compare)

**功能**：
- 并排展示两个 Excel 文件的数据
- 用户可以鼠标点击选择需要比对的列
- 支持设置比对规则（精确匹配、模糊匹配、数值范围等）
- 高亮显示差异行和差异单元格
- 导出比对结果

**使用场景**：
- 比对两个班级的成绩表
- 核对修改前后的数据差异
- 验证数据一致性

### 2. 文件合并模式 (merge)

**功能**：
- 展示所有待合并文件的数据
- 用户可以指定合并方式（纵向追加、横向合并、按列匹配合并）
- 用户可以选择需要合并的列
- 预览合并结果
- 导出合并后的文件

**使用场景**：
- 合并多个班级的成绩表
- 整合多个部门的数据
- 汇总分散的 Excel 文件

### 3. 文件摘要模式 (summary)

**功能**：
- 快速获取文件的基本信息（列名、行数、列数）
- 不加载全部数据，适合大文件
- 输出 JSON 格式的摘要信息

**使用场景**：
- Agent 需要了解文件结构但不需要全部数据
- 预检查文件格式和大小
- 为后续操作提供参数依据

### 4. 结果预览模式 (result) - 待实现

**功能**：
- 处理完成后，根据需求展示结果预览
- 展示处理前后的数据对比
- 高亮显示修改的部分或差异
- 提供导出功能

**使用场景**：
- 用户需要查看处理结果
- 比对完成后查看差异明细
- 合并完成后预览合并结果

**注意**：此模式当前版本暂未实现，结果文件可直接用 Excel 打开查看。后续版本将支持此功能。

## 脚本输出格式

脚本启动后会输出 JSON 格式的启动信息：

```json
{
  "status": "success",
  "mode": "compare",
  "url": "http://localhost:5000",
  "files": ["path/to/file1.xlsx", "path/to/file2.xlsx"],
  "message": "预览服务已启动，请在浏览器中打开上述地址"
}
```

服务运行期间，用户操作结果会保存到指定位置，脚本退出时输出最终结果：

```json
{
  "status": "completed",
  "operation": "compare",
  "output_file": "path/to/comparison_result.xlsx",
  "message": "比对完成，结果已保存"
}
```

## Agent 行为约束

1. **任何表格操作前必须打开 Web 界面确认需求**，使用 `confirm` 操作模式
2. Agent **不需要**详细询问处理规则，这些由用户在网页界面完成
3. 服务启动后，Agent 等待用户完成需求确认并获取配置
4. Agent 根据用户确认的配置生成脚本，确保脚本完全符合用户需求
5. **结果预览按需打开**：根据用户需求决定是否展示结果预览
6. **比对结果只输出分析结果和对比结果**，不复制原始数据

## 使用示例

### 需求确认（必须）

```powershell
# 单个文件需求确认
python skills/excel_preview/scripts/preview_server.py confirm "D:\workspace\project\temp\file1.xlsx"

# 多个文件需求确认
python skills/excel_preview/scripts/preview_server.py confirm "D:\workspace\project\temp\file1.xlsx" "D:\workspace\project\temp\file2.xlsx"

# 目录需求确认（自动递归扫描子目录中的所有 Excel 文件）
python skills/excel_preview/scripts/preview_server.py confirm "D:\workspace\project\测试数据"
```

### 比对两个文件或目录

```powershell
# 比对两个文件
python skills/excel_preview/scripts/preview_server.py compare "D:\workspace\project\temp\file1.xlsx" "D:\workspace\project\temp\file2.xlsx"

# 比对两个目录中的文件（按子目录分组比对）
python skills/excel_preview/scripts/preview_server.py compare "D:\workspace\project\测试数据\标准收取账目" "D:\workspace\project\测试数据\待比对账目"
```

### 合并多个文件

```powershell
python skills/excel_preview/scripts/preview_server.py merge "D:\workspace\project\temp\file1.xlsx" "D:\workspace\project\temp\file2.xlsx" "D:\workspace\project\temp\file3.xlsx"

# 合并目录中的所有文件
python skills/excel_preview/scripts/preview_server.py merge "D:\workspace\project\测试数据\待比对账目"
```

### 结果预览

```powershell
python skills/excel_preview/scripts/preview_server.py result "D:\workspace\project\excel_output\result.xlsx"
```

### 获取文件摘要

```powershell
# 获取单个文件摘要
python skills/excel_preview/scripts/preview_server.py summary "D:\workspace\project\temp\file1.xlsx"

# 获取目录中所有文件摘要（递归扫描）
python skills/excel_preview/scripts/preview_server.py summary "D:\workspace\project\测试数据"
```

### 指定端口号

```powershell
python skills/excel_preview/scripts/preview_server.py confirm "D:\workspace\project\temp\file1.xlsx" --port 8080
```

### 限制加载行数（大文件优化）

```powershell
python skills/excel_preview/scripts/preview_server.py confirm "D:\workspace\project\temp\file1.xlsx" --max-rows 1000
```

## 工作流整合

### 1. 在定制化需求中的使用

```
1. 用户要求处理 Excel 文件
2. Agent 创建工作区并读取文件
3. Agent 调用 data_profile 进行数据探查
4. Agent 调用 excel_preview confirm 启动 Web 服务（必须）
5. 用户在网页界面查看数据预览、选择列、指定规则、填写备注
6. Agent 获取用户确认的需求配置
7. Agent 根据配置生成脚本并执行
8. 保存结果，根据需求决定是否打开结果预览
```

### 2. 在通用化需求中的使用

```
1. 用户提供多个 Excel 文件
2. Agent 创建工作区并读取文件
3. Agent 调用 data_profile 进行数据探查
4. Agent 调用 excel_preview confirm 启动 Web 服务（必须）
5. 用户在网页界面查看所有文件预览、选择比对列、指定规则
6. Agent 获取用户确认的需求配置
7. Agent 根据配置生成比对脚本并执行
8. 保存比对结果，根据需求决定是否打开结果预览
```

## 网页界面功能

### 需求确认界面

- **数据预览区**：展示文件的数据表格，让用户了解数据结构
- **列选择区**：用户可以点击列头选择需要处理的列
- **处理规则区**：
  - 处理类型：比对、合并、筛选、统计等
  - 匹配规则：精确匹配、模糊匹配、数值范围等
  - 其他选项：忽略空值、区分大小写等
- **备注栏**：用户可以填写特殊要求和注意事项
- **确认按钮**：用户确认需求后，配置保存并返回给 Agent

### 比对模式界面

- **文件选择区**：左右两侧分别展示两个文件的数据表格
- **列选择区**：直接点击表格列头选择需要比对的列（红色高亮表示已选中）
- **行选择区**：直接点击行号选择需要比对的行（黄色高亮表示已选中）
- **规则设置区**：
  - 精确匹配：完全相等
  - 模糊匹配：包含关键词
  - 忽略空值：跳过空单元格
- **备注栏**：用户可以填写对比时的注意事项（如特殊处理规则、重点关注项等）
- **差异高亮**：用不同颜色标记差异行和差异单元格
- **确认按钮**：用户确认需求后，配置自动保存到工作区默认输出路径
- **结果导出**：比对结果自动保存到工作区 `excel_output` 目录（无需手动指定路径）

### 合并模式界面

- **文件列表区**：展示所有待合并文件
- **合并方式选择**：
  - 纵向追加：将数据行合并
  - 横向合并：将数据列合并
  - 按列匹配合并：根据关键列匹配合并
- **列选择区**：选择需要合并的列
- **预览区**：预览合并结果
- **结果导出**：导出合并后的 Excel 文件

## 语言切换功能

### Web 界面语言支持

Web 预览界面支持中文/英文双语切换：

- **默认语言**：中文
- **切换方式**：点击页面右上角的地球图标（🌐）
- **语言持久化**：用户的语言选择会保存在浏览器 localStorage 中，下次访问自动应用
- **支持范围**：所有界面元素、按钮文本、提示信息、错误消息等

### Agent 语言适配

当 Agent 检测到用户使用英文发起对话时，应：

1. **全程使用英文交互**：所有回复、解释、错误消息都使用英文
2. **指示 Web 界面切换语言**：在启动 Web 服务时，可以通过 URL 参数或 API 告知界面默认语言
3. **结果文件描述**：比对结果中的说明文字使用英文

**示例**：
```
用户（英文）: "Compare the fee records in folder A with folder B"
Agent（英文）: "I'll help you compare the fee records. Let me start by creating a workspace..."
```

## 注意事项

1. 本技能仅支持 `.xlsx` 和 `.csv` 文件
2. Web 服务默认运行在 localhost，仅本机可访问
3. 服务启动后会自动打开浏览器，用户完成操作后关闭浏览器即可
4. 比对结果和合并结果会自动保存到工作区的 `excel_output` 目录
5. 如果文件较大，加载可能需要几秒钟时间
6. **语言切换**：Web 界面支持中英文切换，点击右上角地球图标即可切换
