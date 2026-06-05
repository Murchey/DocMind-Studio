# Excel-Master

<p align="center">
  <strong>AI 驱动的 Excel 处理助手</strong>
</p>

<p align="center">
  <a href="./README.md">English</a> | <a href="./README_CN.md">中文</a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.9+-blue.svg" alt="Python 3.9+">
  <img src="https://img.shields.io/badge/许可证-GPL%203.0-green.svg" alt="许可证: GPL 3.0">
  <img src="https://img.shields.io/badge/平台-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey.svg" alt="平台">
</p>

---

## 为什么选择 Excel-Master？

**还在手动处理 Excel 文件？** Excel-Master 是一个 AI 助手，可以自动化批量处理、数据分析、表格核对和报告生成。

### 核心优势

- **零学习成本** - 用自然语言描述需求即可
- **可视化确认** - 处理前通过 Web 界面预览数据
- **批量处理** - 同时处理数百个文件
- **智能比对** - 自动匹配不同命名的文件
- **数据可视化** - 自动生成图表和报告

---

## 快速开始

### 1. 安装依赖

```bash
# Windows
install_requirements.bat

# macOS/Linux
pip install -r requirements.txt
```

### 2. 开始使用

只需告诉 AI Agent 你的需求：

```
"比对文件夹A和文件夹B中的账目记录"
"筛选80分以上的学生"
"将所有班级名册合并成一个文件"
```

Agent 会通过可视化 Web 界面引导你完成整个流程。

---

## 使用场景

### 学校
- 比对各班级的收费记录
- 生成学生成绩报告
- 合并多位教师的考勤表

### 企业
- 核对财务记录
- 汇总部门报告
- 分析销售数据趋势

### 任何组织
- 批量处理标准化表格
- 比对数据变更前后差异
- 生成汇总统计

---

## 功能特性

| 功能 | 描述 |
|------|------|
| **批量处理** | 一次性处理数百个 Excel/CSV 文件 |
| **智能比对** | 自动匹配列名进行文件比对 |
| **数据探查** | 分析数据结构和质量 |
| **可视化预览** | 通过 Web 界面查看变更 |
| **图表生成** | 创建柱状图、折线图、饼图、散点图 |
| **格式转换** | 自动将 .xls 转换为 .xlsx |
| **名称匹配** | 匹配不同命名规则的文件 |

---

## 工作流程

```
┌─────────────────────────────────────────────────────────────┐
│  1. 上传文件      →    2. AI 分析     →    3. 预览确认     │
│     (Excel/CSV)         (数据探查)         (Web 界面)      │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  4. 确认规则      →    5. 自动处理   →    6. 下载结果       │
│     (可视化配置)         (自动化)          (结果文件)        │
└─────────────────────────────────────────────────────────────┘
```

---

## 示例工作流

**场景**：比对"标准收费"和"实际缴费"两个目录的账目记录

1. **上传**：将文件放入两个文件夹
2. **分析**：AI 自动检测文件结构
3. **匹配**：系统配对相似名称的文件（如"班级1.xlsx" ↔ "2.1.xlsx"）
4. **配置**：Web 界面显示数据预览，你选择要比对的列
5. **执行**：AI 生成并运行比对脚本
6. **结果**：下载详细的比对报告，差异部分高亮显示

---

## 项目结构

```
Excel-Master/
├─ skills/                    # AI 技能
│  ├─ mkdir_workspace/        # 工作区创建
│  ├─ excel_io/               # Excel 读写
│  ├─ excel_scriptsGen/       # 定制化脚本生成
│  ├─ excel_compare/          # 批量比对
│  ├─ same_name_convertor/    # 智能文件匹配
│  ├─ data_profile/           # 数据分析
│  ├─ excel_compat/           # 格式转换
│  ├─ excel_chart/            # 图表生成
│  └─ excel_preview/          # Web 预览界面
├─ workspace/                 # 自动生成的工作区
├─ requirements.txt           # Python 依赖
├─ AGENT.md                   # AI Agent 工作流（英文）
├─ AGENT_CN.md                # AI Agent 工作流（中文）
└─ README_CN.md               # 本文件
```

---

## 部署指南

### 前置要求
- Python 3.9+
- pip（Python 包管理器）

### 安装步骤

```bash
# 克隆仓库
git clone https://github.com/your-username/excel-master.git
cd excel-master

# 安装依赖
pip install -r requirements.txt

# 或使用批处理文件（Windows）
install_requirements.bat
```

### 配置 AI

配置以下任一 AI 服务：
- **Trae CN**（国内推荐）
- **Qwen Code**
- **Ollama**（本地部署，保护隐私）

---

## 高级功能

### 智能文件匹配

当文件名不同但内容相同时：
- "二（1）班.xlsx" ↔ "2.1.xlsx"
- "第一章.xlsx" ↔ "Chapter1.xlsx"

系统会自动检测并匹配这些文件。

### 数据探查

处理前，系统会分析：
- 列名和数据类型
- 缺失值
- 数据分布
- 样例数据

### 可视化确认

每个操作都需要用户通过 Web 界面确认：
- 处理前预览数据
- 选择特定列
- 配置比对规则
- 查看结果

---

## 常见问题

**Q: 我需要懂 Python 吗？**
A: 不需要！只需用自然语言描述你的需求。

**Q: 我的数据安全吗？**
A: 安全！所有处理都在本地进行。如需更高隐私，可使用 Ollama 本地部署。

**Q: 支持哪些文件格式？**
A: Excel（.xlsx, .xls）和 CSV 文件。

**Q: 能处理几百个文件吗？**
A: 可以！系统专为批量处理设计。

---

## 参与贡献

欢迎贡献代码！请阅读贡献指南。

---

## 许可证

本项目采用 GPL 3.0 许可证 - 详见 [LICENSE](LICENSE) 文件。

---

## 支持

- **问题反馈**：[GitHub Issues](https://github.com/your-username/excel-master/issues)
- **讨论交流**：[GitHub Discussions](https://github.com/your-username/excel-master/discussions)

---

<p align="center">
  为教育工作者、财务人员和数据专业人士倾心打造 ❤️
</p>