---
name: translation-engine
description: 中英互译。
tools: [python]
---

# Translation Engine

文档翻译（中→英 / 英→中）。

**输入**：`optimized_ast` + 语言方向
**输出**：`workspace/translated/translated_ast.json`

---

# 调用方式

```python
import sys
sys.path.insert(0, 'SKILLS/translation-engine/scripts')
from translator import TranslationEngine

engine = TranslationEngine(
    'workspace/parsed/document_ast.json',
    target_language='en'
)
engine.run()
# 输出: workspace/translated/translated_ast.json
```

**参数**：
- `__init__(ast_path, target_language='en')` - AST 路径、目标语言（`en`/`zh`）
- `run()` - 执行翻译

---

# 翻译规则

**可翻译**：正文文本、标题、段落

**禁止翻译**：
- 数学公式
- 代码块
- DOI、URL
- 引用编号
- Figure/Table 编号
- 变量名

---

# 跳过条件

用户选择不翻译时跳过此步骤
