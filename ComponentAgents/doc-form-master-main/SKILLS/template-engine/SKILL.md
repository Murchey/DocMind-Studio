---
name: template-engine
description: 模板管理与加载。
tools: [python]
---

# Template Engine

加载、验证和管理格式模板。

**输入**：用户选择的模板类型
**输出**：`workspace/validated/template_config.json`

---

# 调用方式

```python
import sys
sys.path.insert(0, 'SKILLS/template-engine/scripts')
from template_loader import TemplateLoader

loader = TemplateLoader()
loader.run('chinese_academic.yaml')
# 输出: workspace/validated/template_config.json
```

**参数**：
- `__init__()` - 无参数
- `run(template_name=None)` - 模板文件名（如 `chinese_academic.yaml`）

---

# 模板目录

用户模板：`SKILLS/format-normalizer/custom/`
- `chinese_academic.yaml` - 中文论文
- `english_academic.yaml` - 英文论文

---

# 必需字段

模板必须包含：
- `fonts` - 字体配置（chinese、english、heading）
- `paragraph` - 段落配置（alignment、line_spacing、first_indent）
- `heading` - 标题配置（level1、level2、level3）

---

# 配置结构

```json
{
  "fonts": {"chinese": {"family": "宋体", "size": 12}},
  "paragraph": {"alignment": "justify", "line_spacing": 1.5},
  "heading": {"level1": {"font": "黑体", "size": 16}},
  "toc": {"enabled": true, "max_level": 3},
  "header": {"enabled": true, "text": ""},
  "footer": {"enabled": true, "page_number": true},
  "cover": {"enabled": true, "title": {}, "logo": {}}
}
```

---

# 错误处理

模板缺失/非法 → 使用默认配置、输出警告
