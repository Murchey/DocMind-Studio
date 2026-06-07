---
name: note-complement
description: 文档标注功能，集成在 preview-design 预览界面中，用户可点击页面元素添加修改建议。
tools: [python]
---

# Note Complement

文档标注 SKILL。已集成到 `preview-design` 的预览界面中，无需独立启动服务器。

**功能入口**：preview-design 预览界面右下角浮动按钮"标注笔记"

---

# 工作流概览

```
preview-design 预览界面
    │
    ├─ 用户点击任意预览元素（封面/目录/正文/标题）
    │   → 弹出标注输入框
    │   → 输入修改建议
    │   → 标注添加到面板
    │
    ├─ 用户点击右下角"标注笔记"按钮
    │   → 打开标注面板（右侧滑入）
    │   → 查看/删除所有标注
    │
    └─ 用户点击"保存笔记"或"确认标注"
        → 保存到 workspace/validated/notes.json
```

---

# 调用方式

标注功能集成在 `preview-design` 的 `preview_server.py` 中，通过 `run_preview()` 自动启用。

AGENT 调用方式参见 AGENT.md Step 8 / Step 8b。

---

# 输出格式

`workspace/validated/notes.json`：

```json
{
  "notes": [
    {
      "section": "body",
      "idx": 5,
      "source_text": "原始文本片段...",
      "note": "用户输入的修改建议",
      "created_at": "2026-06-07T12:00:00"
    }
  ]
}
```

---

# 元素分类

| section | 说明 | 示例 |
|---------|------|------|
| cover | 封面页元素 | 学校名称、标题、个人信息 |
| toc | 目录页元素 | 目录条目 |
| body | 正文元素 | 标题、段落、列表 |

---

# API 端点

标注功能在 `preview_server.py` 中提供以下 API：

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/get_notes` | GET | 获取当前所有标注 |
| `/api/add_note` | POST | 添加/更新标注 |
| `/api/delete_note` | POST | 删除标注 |
| `/api/save_notes` | POST | 保存标注到文件 |
| `/api/confirm_notes` | POST | 确认标注并保存 |
