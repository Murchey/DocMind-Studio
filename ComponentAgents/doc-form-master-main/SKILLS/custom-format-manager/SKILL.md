---
name: custom-format-manager
description: 自定义格式配置管理器，提供WEB界面管理格式模板配置
tools: [python]
---

# Custom Format Manager

自定义格式配置管理器，提供 WEB 界面让用户管理格式模板配置。

## 功能

- **配置管理**：查看、创建、编辑、删除、导入、导出格式配置
- **WEB 界面**：现代化的浏览器界面，支持实时编辑和预览
- **模板继承**：基于内置模板创建自定义配置
- **YAML 预览**：实时预览 YAML 格式的配置文件
- **配置导入**：支持从 YAML 文件导入配置

## 使用方法

### 启动 WEB 界面

```python
import sys
sys.path.insert(0, 'SKILLS/custom-format-manager/scripts')
from web_server import run_server

run_server(host='127.0.0.1', port=5001)
```

### 命令行使用

```python
import sys
sys.path.insert(0, 'SKILLS/custom-format-manager/scripts')
from format_manager import FormatManager

manager = FormatManager()

# 列出所有配置
configs = manager.list_configs()

# 加载配置
config = manager.load_config('chinese_academic')

# 保存配置
manager.save_config('my_config', config)

# 另存为新配置
manager.save_as_config('my_custom_config', config)

# 删除配置
manager.delete_config('my_custom_config')

# 导入配置
manager.import_config('path/to/config.yaml', 'imported_config')

# 导出配置
manager.export_config('my_config', 'path/to/output.yaml')
```

## WEB 界面功能

### 配置列表（左侧边栏）
- 显示所有内置和用户自定义配置
- 点击配置加载编辑器
- 新建配置按钮
- 导入配置按钮

### 配置编辑器（右侧面板）
- 分页编辑：基本信息、页面设置、标题样式、正文格式、表格格式、脚注格式、其他设置
- 实时保存
- 另存为新配置
- 删除配置
- 重置修改
- YAML 预览

### 配置项说明

| 分类 | 配置项 | 说明 |
|------|--------|------|
| 基本信息 | metadata.name | 模板名称 |
| 基本信息 | metadata.description | 模板描述 |
| 基本信息 | metadata.standard | 参考标准 |
| 页面设置 | page.size | 页面大小（A4/Letter） |
| 页面设置 | page.margin_* | 页边距（cm） |
| 标题样式 | heading1/2/3.* | 标题字体、字号、对齐等 |
| 正文格式 | body.* | 正文字体、字号、行距、缩进等 |
| 表格格式 | table.* | 表格边框、字体、字号等 |
| 脚注格式 | footnote.* | 脚注字体、字号、编号格式等 |
| 其他设置 | protection.* | 公式、图片、表格保护设置 |

## API 接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/configs` | GET | 获取所有配置列表 |
| `/api/configs/<name>` | GET | 获取指定配置 |
| `/api/configs/<name>` | POST | 保存配置（覆盖） |
| `/api/configs/<name>` | PUT | 另存为新配置 |
| `/api/configs/<name>` | DELETE | 删除配置 |
| `/api/configs/<name>/yaml` | GET | 获取配置的 YAML 格式 |
| `/api/configs/import` | POST | 导入配置 |
| `/api/schema` | GET | 获取配置项结构说明 |

## 配置文件位置

- 内置配置：`SKILLS/format-normalizer/custom/*.yaml`
- 用户配置：`SKILLS/format-normalizer/custom/user/*.yaml`

## 依赖

- Flask
- PyYAML

## 注意事项

- 内置配置（chinese_academic、english_academic）不能直接覆盖，需要另存为新配置
- 用户配置保存在 `user/` 子目录中
- WEB 界面默认端口 5001，可通过参数修改
