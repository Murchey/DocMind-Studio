---
name: doc-compatibility
description: .doc 格式兼容性转换。
tools: [python]
---

# DOC Compatibility

将旧版 .doc 格式文档转换为 .docx 格式，确保后续 Skill 能正常处理。

**输入**：`.doc` 文件路径
**输出**：转换后的 `.docx` 文件

---

# 调用方式

```bash
python SKILLS/doc-compatibility/scripts/doc_converter.py <input_doc_path> [output_docx_path]
```

```python
import sys
sys.path.insert(0, 'SKILLS/doc-compatibility/scripts')
from doc_converter import DocConverter

converter = DocConverter()
result = converter.convert('workspace/input/input.doc', 'workspace/input/input.docx')
# result: {'success': True, 'output_path': 'workspace/input/input.docx', 'method': 'win32com'}
```

**参数**：
- `convert(input_path, output_path=None)` - 转换 .doc 为 .docx
  - `input_path` - 输入 .doc 文件路径
  - `output_path` - 输出 .docx 文件路径（可选，默认覆盖输入路径）
- 返回：转换结果字典

---

# 转换方法

按优先级尝试：

| 优先级 | 方法 | 适用环境 | 依赖 |
|--------|------|----------|------|
| 1 | win32com | Windows + 已安装 Word | `pywin32` |
| 2 | LibreOffice | 跨平台 | LibreOffice 已安装 |
| 3 | Aspose.Words | 跨平台（备选） | `aspose-words` |

---

# 检测逻辑

```python
def is_doc_format(file_path):
    """检测文件是否为 .doc 格式（非 .docx）"""
    ext = Path(file_path).suffix.lower()
    if ext == '.doc':
        return True
    if ext == '.docx':
        return False
    # 尝试读取文件头魔数
    with open(file_path, 'rb') as f:
        header = f.read(8)
        # .doc 格式魔数: D0 CF 11 E0 A1 B1 1A E1
        if header[:4] == b'\xd0\xcf\x11\xe0':
            return True
    return False
```

---

# 输出

```json
{
  "success": true,
  "input_path": "workspace/input/input.doc",
  "output_path": "workspace/input/input.docx",
  "method": "win32com",
  "file_size": 123456
}
```

---

# AGENT 集成

在 AGENT.md 的 Step 1-2（初始化）后、Step 3（解析）前插入：

```
Step 2b: DOC 兼容性检查
- 检测输入文件是否为 .doc 格式
- 如果是 .doc，调用 doc-compatibility 转换为 .docx
- 更新 workspace/input/input.docx 路径
```

---

# 错误处理

- Word/LibreOffice 未安装 → 输出错误信息、提示用户安装
- 文件损坏 → 输出错误日志、保留原文件
- 转换失败 → 中止流程、输出详细错误信息
