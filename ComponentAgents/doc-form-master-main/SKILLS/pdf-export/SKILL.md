---
name: pdf-export
description: DOCX 转 PDF 导出。
tools: [python]
---

# PDF Export

将格式化后的 DOCX 导出为 PDF。

**输入**：格式化后的 DOCX 路径
**输出**：`workspace/output/final.pdf`

---

# 调用方式

```python
import sys
sys.path.insert(0, 'SKILLS/pdf-export/scripts')
from pdf_exporter import PDFExporter

exporter = PDFExporter('workspace/output/formatted.docx')
exporter.run()
# 输出: workspace/output/final.pdf
```

**参数**：
- `__init__(docx_path)` - DOCX 文件路径
- `run()` - 执行 PDF 导出

**备选（docx2pdf）**：
```python
from docx2pdf import convert
convert('workspace/output/formatted.docx', 'workspace/output/final.pdf')
```

---

# 导出引擎

优先级：
1. **Windows**：Microsoft Word COM 接口
2. **跨平台**：LibreOffice headless 模式
3. **备选**：docx2pdf 库

---

# 验证规则

必须验证：
- PDF 文件存在
- PDF 可读取
- 页数大于 0

---

# 安全规则

**禁止**：修改 DOCX 源文件、压缩图片、丢失字体
**必须**：保持排版稳定、图片清晰、公式完整

---

# 错误处理

导出失败 → 输出错误日志、保留原始 DOCX、不输出损坏 PDF
