---
name: preview-design
description: 设计预览与用户确认。
tools: [python, flask]
---

# Preview Design

在浏览器中预览文档设计，等待用户确认。

**输入**：`document_ast` + `template_config` + 源 DOCX 路径
**输出**：用户确认结果 + `edited_config`

---

# 调用方式

## 命令行（推荐，自动打开浏览器等待用户确认）

```bash
python SKILLS/preview-design/scripts/preview_server.py workspace/parsed/document_ast.json workspace/validated/template_config.json workspace/input/input.docx
```

**服务器会**：
1. 启动本地 HTTP 服务（端口 8765-8780）
2. 自动打开浏览器显示预览页面
3. 等待用户在浏览器中编辑配置并点击"确认并继续"
4. 将用户确认的配置保存到 `workspace/validated/edited_config.json`

## Python API

```python
import sys
sys.path.insert(0, 'SKILLS/preview-design/scripts')
from preview_server import run_preview

result = run_preview(
    'workspace/parsed/document_ast.json',
    'workspace/validated/template_config.json',
    'workspace/input/input.docx'
)
# result 包含: user_confirmed, cover_preserved, toc_preserved, edited_config
# edited_config.json 会自动保存到 workspace/validated/
```

**参数**：
- `run_preview(ast_path, template_config_path, source_docx_path=None)`
  - `ast_path` - AST JSON 文件路径
  - `template_config_path` - 模板配置 JSON 文件路径
  - `source_docx_path` - 源 DOCX 文件路径（可选）
- 返回：用户确认的配置 JSON

**重要**：此命令是阻塞式的，会一直等待用户在浏览器中操作。必须使用 `blocking=true` 执行。

**输出文件**：
- `workspace/validated/edited_config.json` - 用户确认/编辑后的配置

---

# 预览内容

必须展示：
1. **封面页**：学校名称、Logo、标题、个人信息
2. **目录页**：已有目录 / 自动生成目录（TOC 域代码）
3. **页眉页脚**：文本、字体、对齐、分隔线、页码
4. **正文样式**：标题/正文字体、字号、行距、缩进
5. **段落间距**：段落之间空行分隔选项

---

# 封面配置

```json
{
  "cover": {
    "enabled": true,
    "school_name": "XX大学",
    "school_font": "宋体",
    "school_size": 18,
    "title": {"text": "课程作业", "font": "黑体", "size": 22},
    "info_items": [{"label": "姓名", "value": ""}],
    "logo": {"enabled": false, "image_data": "", "image_path": ""}
  }
}
```

---

# 服务器规则

端口范围：8765-8780
必须等待服务器启动后再打开浏览器

---

# 安全规则

禁止：访问外部网络、修改源文件
仅允许：读取配置、本地 HTTP 服务
