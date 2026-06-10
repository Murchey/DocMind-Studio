---
name: schedule-export
description: 将排课结果导出为 Excel 文件，支持按教师、班级、教室等维度生成课表
tools: [python]
---

# Schedule Export

将排课结果导出为 Excel 文件，生成可视化的课表。

## 功能说明

- 将排课 JSON 结果转换为 Excel 格式
- 支持多种视图：按班级、按教师、按教室
- 生成格式化的课表，便于打印和查看
- 支持自定义时间表头

## 输入/输出

**输入**：
- `workspace/solution/schedule.json`：排课结果（由 schedule-solver 生成）

**输出**：
- `workspace/output/schedule_by_class.xlsx`：按班级分表的课表
- `workspace/output/schedule_by_teacher.xlsx`：按教师分表的课表
- `workspace/output/schedule_by_room.xlsx`：按教室分表的课表

## 调用方式

```python
import sys
sys.path.insert(0, 'SKILLS/schedule-export/scripts')
from schedule_export import ScheduleExporter

exporter = ScheduleExporter()
exporter.export_all('workspace/solution/schedule.json', 'workspace/output/')
```

```bash
python SKILLS/schedule-export/scripts/schedule_export.py <schedule_json_path> <output_dir> [--view <class|teacher|room>]
```

## 方法参考

| 方法 | 说明 |
|------|------|
| `export_all(schedule_path, output_dir)` | 导出所有视图的课表 |
| `export_by_class(schedule_path, output_path)` | 按班级导出课表 |
| `export_by_teacher(schedule_path, output_path)` | 按教师导出课表 |
| `export_by_room(schedule_path, output_path)` | 按教室导出课表 |

## 输出格式

### 按班级课表

| 时间 | 周一 | 周二 | 周三 | 周四 | 周五 |
|------|------|------|------|------|------|
| 第1节 08:00-08:45 | 高等数学<br/>张老师 A101 | | 高等数学<br/>张老师 A101 | | |
| 第2节 08:55-09:40 | 高等数学<br/>张老师 A101 | | 高等数学<br/>张老师 A101 | | |
| 第3节 10:00-10:45 | | 大学英语<br/>李老师 B201 | | | |
| 第4节 10:55-11:40 | | 大学英语<br/>李老师 B201 | | | |
| ... | ... | ... | ... | ... | ... |

## 依赖

- `openpyxl`：Excel 文件生成

```bash
pip install openpyxl
```

## 错误处理

- 输入文件不存在 → 返回错误信息
- openpyxl 未安装 → 提示安装命令
- 输出目录不存在 → 自动创建
