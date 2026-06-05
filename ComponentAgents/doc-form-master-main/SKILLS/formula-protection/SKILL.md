---
name: formula-protection
description: 数学公式保护。
tools: [python]
---

# Formula Protection

锁定并保护数学公式，防止格式化过程中被修改或删除。

**输入**：`validated_ast` 或 DOCX 文件路径
**输出**：`workspace/normalized/protected_ast.json`

---

# 调用方式

```python
import sys
sys.path.insert(0, 'SKILLS/formula-protection/scripts')
from formula_detector import FormulaDetector

detector = FormulaDetector('workspace/input/input.docx')
detector.run()
# 输出: workspace/normalized/protected_ast.json
```

**参数**：
- `__init__(docx_path)` - DOCX 文件路径
- `run()` - 执行公式检测与保护

---

# 保护内容

必须保护：
- OMML 公式
- MathType 公式
- LaTeX 公式
- Equation Numbering

---

# 安全规则

**禁止**：修改公式内容、删除公式 XML、修改公式 namespace
**必须**：保留公式原始结构、保持公式与文本的关联

---

# 错误处理

公式损坏 → 输出警告日志、保留原公式、继续处理
