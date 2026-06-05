# excel_scriptsGen Skill

```yaml
name: "excel_scriptsGen"
description: "高度定制化 Excel 文件的分析和处理脚本生成，支持 CSV 数据处理与 XLSX 格式/排版调整"
```

---

## 工作流说明

**重要**：在调用 `excel_scriptsGen` 之前，必须先完成以下步骤：

1. **数据探查**：调用 `data_profile` 获取数据特征
2. **需求确认**：调用 `excel_preview confirm` 打开 WEB 页面让用户确认需求
3. **获取配置**：从 `excel_preview` 获取用户确认的需求配置
4. **生成脚本**：根据用户配置调用 `excel_scriptsGen` 生成处理脚本

---

## 主要职责

`excel_scriptsGen` 负责 **根据用户定制需求生成可执行脚本**，用于：

1. **CSV 数据处理**：

   * 数据筛选、排序、计算、清洗
   * 列名/类型标准化
   * 合并、拆分、透视表生成

2. **Excel 排版与格式调整（.xlsx）**：

   * 字体、字号、颜色、单元格边框
   * 列宽、行高调整
   * 表格居中、对齐、冻结窗格
   * 条件格式和高亮异常

3. **工作区生成脚本管理**：

   * 生成的脚本统一保存到：

     ```text
     ./workspace/<user_project_name>/generated_scripts
     ```
   * 保证与 agent 工作流一致，可直接调用 `excel_io` 读取/写入文件

---

## 工作区与路径

* **工作区根路径**：

  ```text
  ./workspace/<user_project_name>/
  ```
* **脚本保存目录**：

  ```text
  ./workspace/<user_project_name>/generated_scripts/
  ```
* **临时 CSV 文件**：

  ```text
  ./workspace/<user_project_name>/temp/
  ```
* **输出 Excel 文件**：

  ```text
  ./workspace/<user_project_name>/excel_output/
  ```

> `<user_project_name>` 为用户在 agent.md 中定义的项目名，AI Agent 根据任务自动替换。

---

## 使用示例

### 1. 生成 CSV 数据处理脚本

```python
from excel_scriptsGen import generate_csv_script

script_path = generate_csv_script(
    input_csv="./workspace/my_project/temp/data.csv",
    operations=[
        {"type": "filter", "column": "成绩", "condition": "<60"},
        {"type": "sort", "column": "学号", "ascending": True},
        {"type": "compute", "column": "总分", "formula": "语文+数学+英语"}
    ],
    output_dir="./workspace/my_project/generated_scripts"
)
print("生成脚本路径：", script_path)
```

### 2. 生成 XLSX 格式/排版调整脚本

```python
from excel_scriptsGen import generate_xlsx_format_script

script_path = generate_xlsx_format_script(
    input_xlsx="./workspace/my_project/temp/data.xlsx",
    formatting_options={
        "font": "微软雅黑",
        "font_size": 11,
        "header_bold": True,
        "column_width": {"学号": 15, "姓名": 20},
        "align": "center",
        "freeze_panes": "A2",
        "highlight_condition": {"column": "成绩", "condition": "<60", "color": "red"}
    },
    output_dir="./workspace/my_project/generated_scripts"
)
print("生成格式脚本路径：", script_path)
```

---

## 参数说明

| 参数                         | 说明                                                              |
| -------------------------- | --------------------------------------------------------------- |
| `input_csv` / `input_xlsx` | 待处理的 CSV 或 Excel 文件绝对路径                                         |
| `operations`               | CSV 数据处理操作列表，每个操作包含 `type` 和相关字段                                |
| `formatting_options`       | Excel 格式化选项，包括字体、字号、列宽、对齐、条件高亮等                                 |
| `output_dir`               | 生成脚本保存路径，默认 `./workspace/<user_project_name>/generated_scripts` |

---

## 注意事项

1. 确保输入文件存在且路径正确。
2. 输出目录需存在，或由 agent 在创建工作区时生成。
3. 生成脚本可以直接被 agent 调用，执行时会在工作区内生成最终 CSV 或 Excel 文件。
4. 支持多种用户自定义规则，可通过自然语言描述或 JSON 操作列表生成脚本。

