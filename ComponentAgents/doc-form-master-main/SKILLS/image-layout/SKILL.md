---
name: image-layout
description: 图片布局优化。
tools: [python]
---

# Image Layout

优化图片在文档中的布局和位置。

**输入**：`normalized_ast` 或 DOCX 文件路径
**输出**：`workspace/optimized/optimized_ast.json`

---

# 调用方式

```python
import sys
sys.path.insert(0, 'SKILLS/image-layout/scripts')
from image_layout import ImageLayoutOptimizer

optimizer = ImageLayoutOptimizer('workspace/input/input.docx')
optimizer.run()
# 输出: workspace/optimized/optimized_ast.json
```

**参数**：
- `__init__(docx_path)` - DOCX 文件路径
- `run()` - 执行图片布局优化

---

# 优化内容

- 图片居中对齐
- 保持图片比例
- 最大宽度 80% 页面宽度
- 避免图片跨页
- 图片与 Caption 保持同页

---

# 配置

```yaml
image:
  alignment: center
  keep_ratio: true
  max_width_percent: 80
  avoid_page_break: true
  keep_with_caption: true
```

---

# 安全规则

**禁止**：压缩图片、删除图片、修改图片内容
**必须**：保留图片 relationship、保持图片清晰度

---

# 跳过条件

用户选择不优化时跳过此步骤
