---
name: "excel_compat"
description: "将旧版 .xls 文件转换为 .xlsx 格式，确保兼容性。当用户要求处理 .xls 文件或需要处理旧版 Excel 文件时调用。"
---

# Excel Compatibility Skill (Excel 兼容性技能)

## 核心目标

将旧版 `.xls` 格式的 Excel 文件转换为现代 `.xlsx` 格式，确保与其他技能（如 `excel_io`、`data_profile`）的兼容性。

## 触发时机

- 用户上传了 `.xls` 格式的 Excel 文件
- 用户需要处理旧版 Excel 文件
- 其他技能检测到 `.xls` 文件并需要转换
- 用户明确要求转换文件格式

## 工具调用方式

- 脚本路径：`skills/excel_compat/scripts/xls_to_xlsx.py`
- 调用命令：`python skills/excel_compat/scripts/xls_to_xlsx.py <源文件路径> [目标文件路径]`

## 参数说明

| 参数 | 必填 | 说明 |
|------|------|------|
| `源文件路径` | 是 | 要转换的 `.xls` 文件的绝对或相对路径 |
| `目标文件路径` | 否 | 转换后的 `.xlsx` 文件保存路径。如不指定，默认保存到源文件同目录，文件名相同但扩展名为 `.xlsx` |

## 脚本输出格式

脚本将输出一段 JSON 格式的字符串，包含以下信息：

- `status`：执行状态（success/error）
- `source_file`：源文件路径
- `target_file`：目标文件路径
- `message`：执行结果描述

### 成功输出示例

```json
{
  "status": "success",
  "source_file": "D:\\data\\old_file.xls",
  "target_file": "D:\\data\\old_file.xlsx",
  "message": "转换成功"
}
```

### 错误输出示例

```json
{
  "status": "error",
  "source_file": "D:\\data\\old_file.xls",
  "target_file": "",
  "message": "文件不存在: D:\\data\\old_file.xls"
}
```

## 转换规则

1. **格式转换**：使用 `xlrd` 读取 `.xls` 文件，使用 `openpyxl` 写入 `.xlsx` 文件
2. **数据保留**：保留所有工作表、单元格数据、合并单元格等
3. **编码处理**：自动处理中文字符和特殊编码
4. **错误处理**：文件不存在、格式错误等情况返回错误信息

## Agent 行为约束

1. 收到 `.xls` 文件时，**必须**先调用此技能进行转换
2. 转换成功后，后续处理使用转换后的 `.xlsx` 文件
3. 转换失败时，向用户报告错误原因并停止处理
4. 如果用户指定的目标路径已存在同名文件，询问用户是否覆盖

## 使用示例

### 基本调用（自动命名）

```powershell
python skills/excel_compat/scripts/xls_to_xlsx.py "D:\data\old_file.xls"
```

### 指定目标路径

```powershell
python skills/excel_compat/scripts/xls_to_xlsx.py "D:\data\old_file.xls" "D:\output\new_file.xlsx"
```

## 工作流整合

### 1. 在文件移动到工作区后调用

当用户上传 `.xls` 文件并移动到工作区 temp 目录后，立即调用此技能进行转换：

```
用户上传 .xls 文件 → 移动到 temp 目录 → 调用 excel_compat 转换 → 使用 .xlsx 文件进行后续处理
```

### 2. 与其他技能配合

- **excel_io**：转换后的 `.xlsx` 文件可直接使用 `excel_io.read()` 读取
- **data_profile**：转换后的 `.xlsx` 文件可直接使用 `data_profile` 进行探查
- **excel_scriptsGen**：转换后的 `.xlsx` 文件可直接用于生成处理脚本

### 3. 批量转换

如果用户上传多个 `.xls` 文件，可以批量调用此技能进行转换：

```powershell
# 伪代码示例
for each xls_file in temp_directory:
    python skills/excel_compat/scripts/xls_to_xlsx.py xls_file
```

## 注意事项

1. 本技能仅支持 `.xls` 格式（Excel 97-2003），不支持 `.xlsx`、`.xlsm` 等格式
2. 转换过程中可能会丢失部分高级格式（如条件格式、数据验证等）
3. 大文件转换可能需要较长时间，请耐心等待
4. 转换后的文件保存在指定位置，原 `.xls` 文件保持不变
5. 如果目标路径已存在同名文件，默认不覆盖，返回错误信息

## 依赖库

- `xlrd`：用于读取 `.xls` 文件
- `openpyxl`：用于写入 `.xlsx` 文件

确保已安装依赖：

```powershell
pip install xlrd openpyxl
```