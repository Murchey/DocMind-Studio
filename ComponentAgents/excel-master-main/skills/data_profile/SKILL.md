---
name: "data_profile"
description: "提取表格数据特征并输出 JSON 格式的探查报告。在进行数据对比、合并、拆分或生成自定义代码之前必须调用，以防止盲目处理导致错误。"
---

# Data Profile Skill (数据探查技能)

## 核心目标

在进行数据对比、合并、拆分或生成自定义代码（Script Gen）之前，**必须**先调用此技能读取表格特征，以防止盲目处理导致错误。

## 触发时机

- 用户上传了新的 Excel 文件并要求处理。
- 用户要求生成定制化的处理逻辑（Script Gen 之前必须执行）。
- 用户询问"这个表里有什么数据"、"表结构是什么"。

## 工具调用方式

- 脚本路径：`skills/data_profile/scripts/data_profile.py`
- 调用命令：`python skills/data_profile/scripts/data_profile.py <文件或目录路径>`

当传入目录路径时，脚本会自动递归扫描所有子目录中的 `.xlsx`、`.xls` 和 `.csv` 文件，输出每个文件的探查报告，并按子目录分组。

## 脚本输出格式解析

脚本将输出一段 JSON 格式的字符串，包含以下关键信息：

- `status`：执行状态（success/error）
- `file_name`：文件名
- `total_rows`：总行数
- `total_cols`：总列数
- `columns`：列级元数据字典，包含：
  - `type`：数据类型（如 object/文本, float64/小数, int64/整数）
  - `null_count`：空值数量（用于判断是否需要清理数据）
  - `unique_count`：去重后的唯一值数量
  - `sample_values`：前 3 个非空样例数据（用于理解该列的实际业务含义，例如看到 "张三" 知道是人名）

## Agent 行为约束

1. 收到本技能的 JSON 结果后，需要在心里构建该表格的物理结构。
2. 发现 `null_count` > 0 时，在生成后续处理脚本时必须加入处理空值的防呆逻辑（如 `fillna` 或 `dropna`）。
3. 如果用户的需求与探查到的 `sample_values` 明显不符（比如用户让计算"姓名"列的总和），需要主动向用户指出矛盾，而不是强行生成报错代码。

## 使用示例

### 调用示例（PowerShell）

```powershell
python skills/data_profile/scripts/data_profile.py "D:\Financial Project\2026_Raw_Data.xlsx"
```

### 输出示例

```json
{
  "status": "success",
  "file_name": "2026_Raw_Data.xlsx",
  "total_rows": 1000,
  "total_cols": 8,
  "columns": {
    "姓名": {
      "type": "object",
      "null_count": 0,
      "unique_count": 950,
      "sample_values": ["张三", "李四", "王五"]
    },
    "年龄": {
      "type": "int64",
      "null_count": 5,
      "unique_count": 50,
      "sample_values": ["25", "30", "35"]
    }
  }
}
```

## 工作流整合

### 1. 定制化需求中的使用

在调用 `excel_scriptsGen` 之前，必须先调用 `data_profile` 获取表格特征，以便生成更精准的处理脚本。

### 2. 通用化需求中的使用

在调用 `excel_compare` 之前，可以调用 `data_profile` 了解表格结构，为比对逻辑提供依据。

### 3. 数据质量检查

当用户询问数据质量或表格结构时，直接调用 `data_profile` 并将 JSON 结果翻译成通俗易懂的语言。

## 注意事项

1. 本技能仅支持 `.xlsx`、`.xls` 和 `.csv` 文件
2. 对于 Excel 文件，默认读取第一个工作表
3. CSV 文件会尝试 UTF-8 和 GBK 两种编码
4. 所有数据按字符串读取，防止精度丢失
5. 输出结果为 JSON 格式，便于 Agent 解析和处理

## 常见问题与解决方案

### 1. 列名不一致问题

**问题描述**：不同来源的 Excel 文件可能有不同的列名结构，导致比对时出现 `KeyError` 错误。

**典型场景**：
- 文件 A 的列名：`['序号', '姓名', '金额']`
- 文件 B 的列名：`['Unnamed: 0', 'Unnamed: 1', 'Unnamed: 2']`

**原因分析**：
- Excel 文件第一行可能是标题行（如"某某学校2025年秋季学期..."），而非表头
- CSV 转换时，表头行被当作数据行，列名自动生成为 `Unnamed: X`

**解决方案**：
1. 检查 `sample_values` 字段：如果第一行数据是"序号"、"姓名"等表头内容，说明需要跳过第一行
2. 使用 `header=None, skiprows=1` 参数读取文件
3. 手动指定列名：`df.columns = ['序号', '姓名', '金额']`

**示例代码**：
```python
# 检测是否需要跳过表头行
df = pd.read_csv(file_path, nrows=3)
if '序号' in df.iloc[0].values or '姓名' in df.iloc[0].values:
    df = pd.read_csv(file_path, header=None, skiprows=1)
    df.columns = ['序号', '姓名', '性别', '学籍号码', '身份证号', '金额', '班级', '备注']
```

### 2. 表头行位置不一致

**问题描述**：不同文件的表头行位置可能不同（有的在第1行，有的在第3行）。

**解决方案**：
1. 使用 `data_profile` 探查每个文件的结构
2. 比较 `sample_values` 字段，判断表头行位置
3. 为每个文件单独指定 `skiprows` 参数

### 3. 列数不一致

**问题描述**：不同文件的列数可能不同，导致合并或比对时出错。

**解决方案**：
1. 检查 `total_cols` 字段
2. 选择列数相同的文件进行比对
3. 或者使用 `pd.merge()` 的 `how='outer'` 参数保留所有列