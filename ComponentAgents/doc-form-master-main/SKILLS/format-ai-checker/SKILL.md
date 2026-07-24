---
name: format-ai-checker
description: XML 格式合规审查 — 通过读取 DOCX XML 内部结构检查格式是否符合中文论文标准。
tools: [python]
---

# Format AI Checker

通过读取 DOCX 文件的 XML 内部结构，检查格式是否符合中文学术论文标准（GB/T 7713.1-2006），并支持自动修复。

**核心原理**：DOCX 本质是 ZIP 包，内含 XML 文件。本 SKILL 直接解析 `word/document.xml`、`word/styles.xml` 等 XML，提取每个段落/运行的完整格式属性（字体、字号、对齐、行距、缩进、颜色等），与规则集逐一比对。发现问题后可自动修复 XML 并重新写入 DOCX。

**优势**：零外部依赖、精确到每个 XML 属性、不依赖视觉渲染、速度快、支持自动修复。

---

# 调用方式

## Python API（推荐）

```python
import sys
sys.path.insert(0, 'SKILLS/format-ai-checker/scripts')
from xml_inspector import XmlInspector

# 仅检查
inspector = XmlInspector(
    docx_path='workspace/output/formatted.docx',
    workspace_dir='workspace'
)
report = inspector.run()

# 检查 + 自动修复（推荐）
inspector = XmlInspector(
    docx_path='workspace/output/formatted.docx',
    workspace_dir='workspace',
    auto_fix=True,        # 启用自动修复
    max_fix_rounds=3      # 最多修复轮数
)
report = inspector.run()
```

**参数**：
- `docx_path` — 待检查的 DOCX 文件路径
- `rules_path` — 规则文件路径（可选，默认使用 `rules/chinese_academic_rules.yaml`）
- `workspace_dir` — 工作区目录（报告输出到 `{workspace_dir}/reports/`）
- `auto_fix` — 启用自动修复（默认 False）
- `max_fix_rounds` — 自动修复最大轮数（默认 3）

**返回**：结构化检查报告 dict（含 `fix_history` 字段记录修复历史）

## 命令行

```bash
python SKILLS/format-ai-checker/scripts/xml_inspector.py workspace/output/formatted.docx [rules_path] [workspace_dir]
```

---

# Content Validator — 内容乱码校验（新增）

通过检测 MD 源文件和 DOCX 输出文件，预防和发现因 pandoc 转换导致的乱码问题。

**典型场景**：MD 文件中嵌入了 raw JSON 数据（含 `\\` 反斜杠路径），pandoc 在 MD→DOCX 时将 `\\` 解释为转义符，导致路径信息丢失和乱码。

## 检测规则

| 规则 | 阶段 | 严重度 | 说明 |
|------|------|--------|------|
| RAW_JSON_BLOB | 预检 | ERROR | 嵌入的 JSON/代码块中包含反斜杠转义符 |
| BACKSLASH_PATH | 预检 | ERROR | 文本中包含 Windows 反斜杠路径 |
| OVERSIZE_PARAGRAPH | 预检 | WARNING | 段落过长（>5000 chars），pandoc 可能截断 |
| GARBLED_DOLLAR | 预检/后检 | ERROR | 连续 $$$ 符号 — 反斜杠被吃掉的乱码特征 |
| JSON_RESIDUE | 后检 | ERROR | DOCX 中残留 JSON 片段 |
| PARAGRAPH_MISMATCH | 后检 | WARNING | DOCX 段落数远少于源 MD（覆盖率 <30%） |
| TABLE_CORRUPTION | 后检 | WARNING | MD 含表格但 DOCX 中无任何表格 |

## CLI 调用

```bash
# 预检（MD→DOCX 转换前）
python SKILLS/format-ai-checker/scripts/content_validator.py pre source.md

# 后检（转换后检查 DOCX）
python SKILLS/format-ai-checker/scripts/content_validator.py post output.docx source.md

# 全流程（预检 + 后检）
python SKILLS/format-ai-checker/scripts/content_validator.py full source.md output.docx
```

**返回值**：JSON 报告，含 status（PASS/WARN/FAIL）、issues 列表、summary。
**退出码**：0（PASS/WARN）、1（FAIL）

## Python API

```python
from content_validator import ContentValidator

validator = ContentValidator()

# 预检
report = validator.pre_check_md("report.md")
if report.has_errors():
    print("存在严重问题，请修复后再转换")
    for issue in report.issues:
        print(f"  [{issue.severity}] {issue.category}: {issue.message}")

# 后检
report = validator.post_check_docx("report.docx", "report.md")
if report.status == "PASS":
    print("DOCX 内容校验通过，无乱码")

# 全流程
report = validator.check("report.md", "report.docx")
report.print_summary()
```

## 集成到 AGENT 流程

在 doc-form-master 的 MD→DOCX 转换前后各调用一次：

```
Step: MD→DOCX 转换
  ├── [前] content_validator pre_check      ← 提前拦截问题
  ├── markitdown_converter md→docx
  └── [后] content_validator post_check     ← 验证输出无乱码
       └── 如果 FAIL → 提示修复源 MD → 重新转换
```

---

# 检查流程

```
DOCX → ZIP 解包 → XML 解析 → 格式属性提取 → 规则比对 → 结构化报告
                                                          ↓ (auto_fix=True)
                                                    自动修复 → 重新检查 → 循环直到 A/A-
```

1. **XML 解析**（`docx_xml_reader.py`）：
   - 以 ZIP 方式打开 DOCX
   - 解析 `word/document.xml` — 提取每个 `<w:p>` 的完整格式属性
   - 解析 `word/styles.xml` — 解析样式定义层级
   - 解析 `<w:sectPr>` — 页面尺寸、页边距
   - 解析 `<w:tbl>` — 表格边框、单元格格式
   - 样式层级合并：直接格式化 > 样式定义

2. **规则比对**（`rule_engine.py`）：
   - 加载规则集（YAML）
   - 逐项检查文档格式属性
   - 输出问题列表（含严重级别、位置、建议）

3. **报告生成**（`xml_inspector.py`）：
   - JSON 报告：完整结构化数据
   - Markdown 报告：人类可读格式
   - 综合评级：A / A- / B / C / D

4. **自动修复**（`docx_fixer.py`，`auto_fix=True` 时触发）：
   - 直接修改 DOCX ZIP 中的 `word/document.xml`
   - 修复字体（中文字体、英文字体、字号、粗体）
   - 修复段落格式（对齐、首行缩进）
   - 修复页面边距
   - 修复表格（三线表格式、表头/表体字体）
   - 修复标题颜色（强制黑色）
   - 修复后重新检查，循环直到 A/A- 或达到最大轮数

---

# 检查规则

## 页面布局（severity: critical）

| 规则 | 标准 | 容差 |
|------|------|------|
| 页面尺寸 | A4（210×297mm） | ±5mm |
| 上边距 | 2.54cm | ±0.3cm |
| 下边距 | 2.54cm | ±0.3cm |
| 左边距 | 3.17cm | ±0.3cm |
| 右边距 | 2.54cm | ±0.3cm |

## 字体（severity: critical）

| 位置 | 中文字体 | 英文字体 | 字号 | 粗体 |
|------|---------|---------|------|------|
| 正文 | 宋体 | Times New Roman | 12pt | 否 |
| 一级标题 | 黑体 | — | 14pt | 是 |
| 二级标题 | 黑体 | — | 12pt | 是 |
| 三级标题 | 黑体 | — | 12pt | 是 |

**颜色检查**：标题颜色强制黑色（RGB 000000）

## 段落格式（severity: critical）

| 规则 | 标准 |
|------|------|
| 对齐方式 | 两端对齐（both） |
| 行距 | 1.5 倍 |
| 首行缩进 | 2 字符（约 480 twips） |
| 段前间距 | 0pt |
| 段后间距 | 0pt |

## 标题格式

| 级别 | 对齐 | 段前 | 段后 | 缩进 |
|------|------|------|------|------|
| H1 | 居中 | 24pt | 18pt | 无 |
| H2 | 左对齐 | 18pt | 12pt | 无 |
| H3 | 左对齐 | 6pt | 6pt | 无 |

## 表格（severity: warning）

| 规则 | 标准 |
|------|------|
| 边框样式 | 三线表（顶/底线粗，栏目线细，无竖线） |
| 表头字体 | 黑体 10.5pt 加粗 |
| 表体字体 | 宋体 10.5pt |

## 文档结构

| 规则 | 要求 |
|------|------|
| 章编号 | H1 匹配 `第X章` 格式 |
| 连续空段 | 最多 2 个 |
| 参考文献 | 文档末尾应存在 |

---

# 规则文件

规则文件位于 `rules/chinese_academic_rules.yaml`，可自定义修改：

```yaml
# 修改正文字体为仿宋
fonts:
  body:
    chinese_family: 仿宋

# 修改页面边距
page:
  margins:
    top_cm: 3.0
    left_cm: 2.8
```

支持的 severity 级别：
- `critical` — 必须修复，影响格式合规
- `warning` — 建议修复
- `info` — 仅记录

---

# 报告输出

## JSON 报告（`{workspace}/reports/xml_inspection_report.json`）

```json
{
  "check_time": "2026-07-21T15:30:00",
  "overall_grade": "B",
  "summary": {
    "total_issues": 8,
    "critical": 2,
    "warnings": 4,
    "suggestions": 2
  },
  "critical_issues": [
    {
      "category": "font",
      "severity": "critical",
      "rule": "中文字体应为 宋体",
      "expected": "宋体",
      "actual": "楷体",
      "location": "段落 5: \"这是一段测试文本...\"",
      "suggestion": "将字体从 楷体 改为 宋体"
    }
  ],
  "by_category": {
    "font": {"count": 3, "critical": 1, "warnings": 2},
    "paragraph": {"count": 2, "critical": 1, "warnings": 1}
  }
}
```

## Markdown 报告（`{workspace}/reports/xml_inspection_report.md`）

人类可读的格式化报告，含表格、分级问题列表。

## 评级标准

| 评级 | 条件 |
|------|------|
| A | 无严重问题，无警告 |
| A- | 无严重问题，警告 ≤5 |
| B | 严重问题 ≤1 或 警告 >5 |
| C | 严重问题 2-5 |
| D | 严重问题 >5 |

---

# 与现有 SKILL 的关系

| SKILL | 关系 |
|-------|------|
| `format-normalizer` | **前置**：格式化后交给本 SKILL 检查 |
| `zero-format-normalizer` | **前置**：零格式标准化后检查 |
| `preview-design` | **互补**：preview 是格式化前预览，本 SKILL 是格式化后审查 |
| `docx-parser` | **相似**：parser 提取 AST，本 SKILL 提取完整 XML 格式属性用于合规检查 |

---

# 调用位置（AGENT 流程）

在 AGENT.md 执行流程中，本 SKILL 在 **Step 9a/9b 之后、Step 10 之前** 触发：

```
Step 9a: 格式标准化（format-normalizer / zero-format-normalizer）
Step 9b: 表格格式化（table-processor）
🆕 Step 9d: XML 格式合规检查 + 自动修复（format-ai-checker）
  → 检查并生成报告
  → auto_fix=True 时自动修复 XML 并重新检查
  → 循环直到 A/A- 或达到最大轮数
  → 最终报告保存到 workspace/reports/
Step 10: 后续处理（image-layout / pdf-export）
```

---

# 文件结构

```
SKILLS/format-ai-checker/
├── SKILL.md                          # 本文档
├── scripts/
│   ├── xml_inspector.py              # 主入口（检查 + 自动修复循环）
│   ├── docx_xml_reader.py            # DOCX XML 解析器（ZIP → 格式属性）
│   ├── rule_engine.py                # 规则引擎（YAML → 逐项比对）
│   ├── docx_fixer.py                 # 自动修复器（XML 级别修改 DOCX）
│   └── content_validator.py          # ⭐ 内容乱码校验器（MD预检 + DOCX后检）
└── rules/
    └── chinese_academic_rules.yaml   # 中文学术论文格式规则集
```

---

# 依赖

| 依赖 | 版本 | 用途 |
|------|------|------|
| lxml | ≥4.6 | XML 解析 |
| Python | ≥3.6 | 标准库（zipfile, json, re, pathlib） |

**无外部系统依赖**：不需要 LibreOffice、Word、poppler 等。

---

# 错误处理

| 场景 | 处理 |
|------|------|
| DOCX 文件不存在 | 抛出 FileNotFoundError |
| DOCX 损坏/无法解压 | 捕获 BadZipFile，输出错误 |
| 无 sectPr（无页面属性） | 使用 A4 默认值，输出警告 |
| 规则文件不存在 | 使用内置默认规则 |
| lxml 未安装 | 输出安装提示 |
