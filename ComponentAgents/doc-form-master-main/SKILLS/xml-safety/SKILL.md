---
name: xml-safety
description: XML 安全校验。
tools: [python]
---

# XML Safety

验证 DOCX XML 结构安全性。验证失败则停止处理。

**输入**：`document_ast` 或 DOCX 文件路径
**输出**：`workspace/validated/validated_ast.json`

---

# 调用方式

```python
import sys
sys.path.insert(0, 'SKILLS/xml-safety/scripts')
from xml_validator import XMLSafetyValidator

validator = XMLSafetyValidator('workspace/input/input.docx')
validator.run()
# 输出: workspace/validated/validated_ast.json
```

**参数**：
- `__init__(docx_path)` - DOCX 文件路径
- `run()` - 执行验证，输出验证结果

---

# 验证内容

必须验证：
- styles.xml 存在且合法
- numbering.xml 存在且合法
- relationships 完整
- namespace 正确
- section properties 有效

---

# 安全规则

**禁止**：修改 relationship id、删除 namespace、删除 style 引用
**必须**：保留原始 XML 结构、不修改 document.xml

---

# 错误处理

验证失败 → 输出错误日志、停止后续处理、保留原文件
