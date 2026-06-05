---
name: "same_name_convertor"
description: "解析比对文件时的两组文件名，把相同语义的文件名转换为同名文件对。在执行比对任务之前必须调用，确保两个目录中的文件能够正确配对。"
---

# Same Name Convertor Skill (同名文件转换技能)

## 核心目标

在执行比对任务之前，解析两个目录中的文件名，识别语义相同但命名不同的文件，并将它们转换为同名文件对，确保比对时能够正确配对。

## 触发时机

- **比对任务执行前必须调用**：在 `excel_preview compare` 之前执行
- 两个目录中的文件名不完全一致，但语义相同
- 需要批量重命名文件以便后续比对

## 典型场景

### 场景1：命名格式不同

```
目录A（标准收取账目）：
├── 二（1）班.xlsx
├── 二（2）班.xlsx
└── 二（3）班.xlsx

目录B（待比对账目）：
├── 2.1.xlsx
├── 2.2.xlsx
└── 2.3.xlsx

→ 语义映射：二（1）班 ↔ 2.1, 二（2）班 ↔ 2.2, 二（3）班 ↔ 2.3
```

### 场景2：包含多余前缀/后缀

```
目录A：
├── 2025年秋季_班级1.xlsx
├── 2025年秋季_班级2.xlsx

目录B：
├── 班级1_缴费记录.xlsx
├── 班级2_缴费记录.xlsx

→ 语义映射：2025年秋季_班级1 ↔ 班级1_缴费记录
```

### 场景3：编号格式不同

```
目录A：
├── 第一章.xlsx
├── 第二章.xlsx

目录B：
├── Chapter1.xlsx
├── Chapter2.xlsx

→ 语义映射：第一章 ↔ Chapter1, 第二章 ↔ Chapter2
```

## 工具调用方式

- 脚本路径：`skills/same_name_convertor/scripts/same_name_convertor.py`
- 调用命令：`python skills/same_name_convertor/scripts/same_name_convertor.py <目录A路径> <目录B路径> [--output 输出目录] [--strategy 策略]`

## 参数说明

| 参数 | 必填 | 说明 |
|------|------|------|
| `目录A路径` | 是 | 第一个目录的绝对路径 |
| `目录B路径` | 是 | 第二个目录的绝对路径 |
| `--output` | 否 | 输出目录路径，默认为工作区 temp 目录 |
| `--strategy` | 否 | 匹配策略：`auto`（自动）、`number`（数字提取）、`keyword`（关键词匹配）、`manual`（手动配置）。默认 `auto` |
| `--config` | 否 | 手动配置文件路径（JSON格式），用于 `manual` 策略 |

## 匹配策略

### 1. 自动策略 (auto) - 默认

自动分析文件名特征，选择最合适的匹配方式：
1. 尝试提取文件名中的数字进行匹配
2. 如果数字匹配失败，尝试关键词匹配
3. 如果仍然失败，提示用户手动配置

### 2. 数字提取策略 (number)

从文件名中提取数字，按数字进行匹配：
- `二（1）班.xlsx` → 提取数字 `1`
- `2.1.xlsx` → 提取数字 `2`, `1`（取最后一组数字 `1`）

### 3. 关键词匹配策略 (keyword)

提取文件名中的关键词（如班级名、章节名），进行模糊匹配：
- `二（1）班.xlsx` → 关键词 `二`, `1`, `班`
- `2.1班.xlsx` → 关键词 `2`, `1`, `班`

### 4. 手动配置策略 (manual)

用户提供 JSON 配置文件，手动指定文件映射关系：

```json
{
  "mapping": [
    {"left": "二（1）班.xlsx", "right": "2.1.xlsx"},
    {"left": "二（2）班.xlsx", "right": "2.2.xlsx"}
  ]
}
```

## 脚本输出格式

脚本将输出 JSON 格式的结果：

```json
{
  "status": "success",
  "strategy": "auto",
  "total_left": 8,
  "total_right": 8,
  "paired_count": 8,
  "unpaired_left": [],
  "unpaired_right": [],
  "mapping": [
    {"left": "二（1）班.xlsx", "right": "2.1.xlsx", "confidence": 0.95},
    {"left": "二（2）班.xlsx", "right": "2.2.xlsx", "confidence": 0.95}
  ],
  "renamed_dir": "d:\\workspace\\project\\temp\\renamed",
  "message": "文件名转换完成，已创建同名文件对"
}
```

## 输出目录结构

转换后的文件会复制到输出目录，保持两个子目录结构：

```
<output_dir>/
├── left/           # 左侧目录的文件（已重命名）
│   ├── 2.1.xlsx
│   ├── 2.2.xlsx
│   └── ...
└── right/          # 右侧目录的文件（保持原名）
    ├── 2.1.xlsx
    ├── 2.2.xlsx
    └── ...
```

## Agent 行为约束

1. **比对任务前必须调用**：确保两个目录中的文件能够正确配对
2. 如果自动匹配失败或置信度过低（< 0.8），必须询问用户确认
3. 如果存在未配对的文件，必须告知用户并询问处理方式
4. 转换完成后，使用输出目录中的文件进行后续比对
5. 原始文件不会被修改，只在输出目录中创建副本

## 工作流整合

### 在通用化需求中的使用

```
1. 用户提供两个目录的文件
2. Agent 创建工作区并读取文件
3. Agent 调用 same_name_convertor 解析文件名并创建同名文件对
4. Agent 调用 data_profile 进行数据探查
5. Agent 调用 excel_preview compare 让用户确认比对需求（使用转换后的目录）
6. Agent 根据配置生成比对脚本并执行
7. 保存比对结果
```

## 注意事项

1. 原始文件不会被修改，只创建副本
2. 如果文件名完全相同，无需调用此技能
3. 对于大量文件（> 50），建议使用 `auto` 策略并人工确认
4. 转换后的文件会保留原始文件的目录结构
5. 如果匹配失败，脚本会输出详细的错误信息供排查

## 依赖库

- `pandas`：用于数据处理
- `openpyxl`：用于读取 Excel 文件
- `difflib`：用于字符串相似度计算（Python 标准库）
- `re`：用于正则表达式匹配（Python 标准库）

确保已安装依赖：

```powershell
pip install pandas openpyxl
```