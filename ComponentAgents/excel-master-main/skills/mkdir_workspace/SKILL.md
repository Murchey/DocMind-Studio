# mkdir_workspace Skill

```yaml
name: "mkdir_workspace"
description: "在工作区创建用户项目及标准子目录，用于 Excel 文件处理流程"
```

---

## 主要职责

`mkdir_workspace` 负责 **在工作区创建项目目录及标准子目录**，为 Excel 文件处理和定制脚本生成提供统一环境。

### 创建目录结构示例

```text
./workspace/<user_project_name>/
├─ temp/                  # 临时 CSV 或中间文件
├─ generated_scripts/     # 定制化处理脚本
└─ excel_output/          # 输出 Excel 文件或分析报告
```

> `<user_project_name>` 由 agent 根据用户项目名自动替换。

---

## 调用脚本说明

### PowerShell 版本（推荐）

* **脚本路径**：`mkdir_workspace.ps1`
* **功能**：创建工作区及 `temp`、`generated_scripts`、`excel_output` 子目录
* **自动处理**：如果目录已存在，不覆盖，保证数据安全

**命令示例**：

```powershell
# 进入脚本目录
cd D:\workspace_scripts

# 创建项目名为 my_project 的工作区
.\mkdir_workspace.ps1 -ProjectName "my_project"
```

**参数说明**：

* `ProjectName`：用户项目名，必填
* `BasePath`：工作区根路径，可选，默认 `.\workspace`

---

### CMD 批处理版本（可选）

* **脚本路径**：`mkdir_workspace.bat`
* **功能**：与 PowerShell 脚本同等，适合不支持 PowerShell 的环境

**命令示例**：

```cmd
cd D:\workspace_scripts
mkdir_workspace.bat my_project
```

---

## Python 调用示例（可选封装）

```python
from mkdir_workspace import create_workspace

workspace_path = create_workspace(user_project_name="my_project")
print(f"工作区已创建：{workspace_path}")
```

* Python 封装可以调用 PowerShell 或直接使用 `os.makedirs()` 创建目录

---

## 注意事项

1. 工作区路径应可写，否则创建失败
2. 用户项目名应避免特殊字符和系统保留字符
3. 目录已存在时，不覆盖已有文件，保证数据安全
4. **此 Skill 是其他 Excel Skill 的前置条件**，必须先执行，保证工作区环境完整

