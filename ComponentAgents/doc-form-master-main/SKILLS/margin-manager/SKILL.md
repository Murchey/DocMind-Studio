---
name: margin-manager
description: 页边距管理，支持党政机关公文和学术论文标准。
tools: [python]
---

# Margin Manager

页边距管理 Skill，支持国家标准页边距设置。

**输入**：DOCX 文件路径 + 页边距标准
**输出**：设置页边距后的 DOCX 文件

---

# 调用方式

## Python API

```python
import sys
sys.path.insert(0, 'SKILLS/margin-manager/scripts')
from margin_manager import MarginManager

manager = MarginManager()

# 应用公文标准
result = manager.apply_margins('input.docx', standard='government')

# 应用学术论文标准
result = manager.apply_margins('input.docx', standard='academic')

# 自定义页边距
result = manager.apply_margins('input.docx', margins={
    'top': 3.0,    # 厘米
    'bottom': 3.0,
    'left': 2.5,
    'right': 2.5
})
```

**参数**：
- `apply_margins(docx_path, standard=None, margins=None, output_path=None)` - 应用页边距
  - `docx_path` - DOCX 文件路径
  - `standard` - 预设标准（'government' 或 'academic'）
  - `margins` - 自定义页边距字典（厘米）
  - `output_path` - 输出路径（可选，默认覆盖原文件）
- 返回：操作结果字典

---

# 页边距标准

## 党政机关公文标准（GB/T 9704-2012）

| 项目 | 值 | 说明 |
|------|-----|------|
| 纸张大小 | A4 (210mm × 297mm) | 国家标准 |
| 上边距 | 3.7 cm (37mm) | 国家标准 |
| 下边距 | 3.5 cm (35mm) | 国家标准 |
| 左边距 | 2.8 cm (28mm) | 国家标准 |
| 右边距 | 2.6 cm (26mm) | 国家标准 |
| 版心尺寸 | 156mm × 225mm | 计算得出 |
| 每面行数 | 22 行 | 撑满版心 |
| 每行字数 | 28 字 | 撑满版心 |

## 国内学术论文标准

| 项目 | 值 | 说明 |
|------|-----|------|
| 纸张大小 | A4 (210mm × 297mm) | 通用标准 |
| 上边距 | 2.54 cm | 常见参考值 |
| 下边距 | 2.54 cm | 常见参考值 |
| 左边距 | 3.17 cm | 预留装订空间 |
| 右边距 | 3.17 cm | 对称设置 |

---

# 预设标准

| 标准名称 | 标识 | 上 | 下 | 左 | 右 |
|----------|------|-----|-----|-----|-----|
| 党政机关公文 | `government` | 3.7 | 3.5 | 2.8 | 2.6 |
| 学术论文 | `academic` | 2.54 | 2.54 | 3.17 | 3.17 |
| 镜像页边距 | `mirror` | 2.54 | 2.54 | 2.5 | 2.0 |

---

# 输出格式

```json
{
  "success": true,
  "docx_path": "input.docx",
  "standard": "government",
  "margins": {
    "top": 3.7,
    "bottom": 3.5,
    "left": 2.8,
    "right": 2.6
  },
  "sections_modified": 1
}
```

---

# AGENT 集成

在 AGENT.md 的 Step 9a/9b（格式化）后插入：

```
Step 9c: 页边距设置
- 根据文档类型（公文/学术论文）选择页边距标准
- 应用标准页边距到所有节
```

---

# 错误处理

- 文件不存在 → 输出错误信息
- 无效标准 → 使用默认学术论文标准
- 节处理失败 → 跳过该节、输出警告
