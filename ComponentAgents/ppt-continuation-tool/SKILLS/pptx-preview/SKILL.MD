---
name: pptx-preview
description: 提供PPTX文件的浏览器预览功能，支持幻灯片浏览和基本交互
tools: [python]
---

# PPTX Preview

提供PPTX文件的浏览器预览功能，支持幻灯片浏览和基本交互。

## 功能说明

本SKILL负责PPT续写流程的预览阶段，包括：
1. 将PPTX文件转换为可在浏览器中预览的格式
2. 提供幻灯片浏览界面
3. 支持基本的幻灯片交互（前进、后退、跳转）
4. 支持预览续写后的完整PPT

## 输入/输出

**输入**：
- `{workspace}/output/*.pptx`：续写完成的PPTX文件
- `{workspace}/input/*.pptx`：原始半完成PPT（可选）

**输出**：
- 浏览器预览界面（本地服务器）
- `{workspace}/preview/`：预览资源目录

## 脚本说明

### pptx_preview_server.py
PPTX预览服务器，将PPTX转换为可在浏览器中预览的格式。

```bash
# 启动预览服务器
python3 SKILLS/pptx-preview/scripts/pptx_preview_server.py <pptx_file> [--port 5050]

# 预览工作区中的PPTX文件
python3 SKILLS/pptx-preview/scripts/pptx_preview_server.py {workspace}/output/*.pptx --port 5050
```

## 执行流程

### Step 1: 启动预览服务器
```python
import sys
sys.path.insert(0, 'SKILLS/pptx-preview/scripts')
from pptx_preview_server import start_preview_server

# 启动预览服务器
server_url = start_preview_server(
    pptx_path='{workspace}/output/*.pptx',
    port=5050,
    auto_open=True
)
print(f"预览服务器已启动: {server_url}")
```

### Step 2: 提供预览信息
```python
# 告知用户预览地址
preview_info = {
    "url": "http://localhost:5050",
    "slides": total_slides,
    "features": [
        "幻灯片浏览",
        "前进/后退导航",
        "跳转到指定幻灯片",
        "全屏模式"
    ]
}
```

## 预览功能

### 基本功能
- **幻灯片浏览**：逐页查看PPT内容
- **导航控制**：前进、后退、首页、末页
- **跳转功能**：直接跳转到指定幻灯片
- **全屏模式**：全屏查看幻灯片

### 交互功能
- **键盘快捷键**：
  - 左箭头/上箭头：上一张幻灯片
  - 右箭头/下箭头：下一张幻灯片
  - Home：第一张幻灯片
  - End：最后一张幻灯片
  - F11：全屏切换
  - Esc：退出全屏

### 显示信息
- 当前幻灯片编号/总页数
- 幻灯片标题（如有）
- 预览控制按钮

## 输出格式

### 预览服务器信息
```json
{
  "status": "running",
  "url": "http://localhost:5050",
  "pptx_file": "output.pptx",
  "total_slides": 15,
  "port": 5050
}
```

## 注意事项

1. 预览服务器默认在本地运行（127.0.0.1）
2. 默认端口为5050，可通过--port参数修改
3. 预览服务器会持续运行直到用户关闭或程序终止
4. 预览功能仅用于查看，不支持编辑
5. 预览资源在服务器关闭后自动清理