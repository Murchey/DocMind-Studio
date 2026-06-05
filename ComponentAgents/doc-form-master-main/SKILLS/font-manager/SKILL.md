---
name: font-manager
description: 字体兼容管理。
tools: [python]
---

# Font Manager

检测系统字体、验证模板字体、自动 fallback。

**输入**：`template_config`
**输出**：`workspace/validated/font_mapping.json`

---

# 调用方式

```python
import sys
sys.path.insert(0, 'SKILLS/font-manager/scripts')
from font_detector import FontManager

manager = FontManager()
manager.run()
# 输出: workspace/validated/font_mapping.json
```

**参数**：
- `__init__()` - 无参数（自动读取 `workspace/validated/template_config.json`）
- `run()` - 执行字体检测与映射

---

# 检测内容

必须检测：中文字体、英文字体、等宽字体

---

# 优先字体

- **中文**：宋体、黑体、仿宋_GB2312、楷体、微软雅黑
- **英文**：Times New Roman、Arial、Calibri、Cambria
- **等宽**：Consolas、Courier New

---

# Fallback 规则

字体缺失时自动 fallback：
- 宋体 → SimSun → Noto Serif CJK SC
- 黑体 → SimHei → Noto Sans CJK SC
- Times New Roman → Liberation Serif

---

# 输出

```json
{
  "available_fonts": [],
  "missing_fonts": [],
  "font_mapping": {"宋体": "SimSun"}
}
```

---

# 错误处理

字体缺失 → 自动 fallback、输出警告、不中断流程
