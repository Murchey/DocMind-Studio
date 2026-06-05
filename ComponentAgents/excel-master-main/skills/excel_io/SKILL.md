# excel_io Skill
---
name: "excel_io"
description: "Excel 文件的读取、保存和工作区适配操作"
---

## 主要职责

`excel_io` 负责 Excel 文件在 **工作区内的读取、临时保存和输出**，供其他 Skill 调用。

* **读取 Excel** → 转为 CSV 或 DataFrame
* **保存 Excel** → 将 DataFrame 或分析结果保存为 Excel
* **工作区适配** → 支持保存到默认工作区输出目录或用户指定路径

---

## 1. 读取 Excel 文件

**功能说明**：

* 将指定路径的 Excel 文件读取为 CSV 或 Pandas DataFrame
* 支持多 Sheet 或指定 Sheet 读取
* 保存中间 CSV 文件到工作区或临时目录
* **支持递归扫描子目录**：当源路径为目录时，自动递归扫描所有子目录中的 Excel 文件，并在目标目录中保留子目录结构

**调用示例（PowerShell）**：

```powershell
# 读取单个文件
python skills/excel_io/scripts/excel_read.py "D:\Financial Project\2026_Raw_Data.xlsx" "D:\workspace\user_project_name\temp"

# 读取目录中所有文件（递归扫描子目录，保留目录结构）
python skills/excel_io/scripts/excel_read.py "D:\Financial Project\测试数据" "D:\workspace\user_project_name\temp"
```

## 2. 保存 Excel 文件

**功能说明**：

* 将 DataFrame 或分析结果保存为 Excel 文件
* 支持保存到工作区输出目录或用户指定路径
* 可设置输出文件名和 Sheet 名称

**调用示例（PowerShell）**：

```powershell
python write_excel.py "D:\workspace\user_project_name\temp\processed.csv" "D:\workspace\user_project_name\excel_output\result.xlsx"
```

## 3. 工作区适配（与 agent.md 配合）

* 默认读取/保存路径均可指定为 **工作区目录**：
  * 工作区目录：`./workspace/user_project_name`
  * 临时文件：`./workspace/user_project_name/temp`
  * 输出文件：`./workspace/user_project_name/excel_output`
* 如果用户指定路径，Skill 自动覆盖默认目录
* AI Agent 可以通过参数切换默认保存目录或用户指定目录