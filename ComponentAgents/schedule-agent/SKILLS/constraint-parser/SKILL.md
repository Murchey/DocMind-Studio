---
name: constraint-parser
description: 解析 Markdown 文档中的排课约束条件，提取教师、课程、教室、时间等信息
tools: [python]
---

# Constraint Parser

解析 Markdown 文档中的排课约束条件，将非结构化的排课需求转换为结构化的 JSON 数据。

## 功能说明

- 解析 MD 文档中的排课约束
- 提取教师、课程、教室、时间槽等信息
- 识别硬约束（必须满足）和软约束（尽量满足）
- 输出标准化的 JSON 约束文件

## 输入/输出

**输入**：
- `workspace/input/*.md`：排课需求文档（一个或多个）

**输出**：
- `workspace/parsed/constraints.json`：结构化约束数据
- `workspace/parsed/summary.md`：解析摘要（人类可读）

## 调用方式

```python
import sys
sys.path.insert(0, 'SKILLS/constraint-parser/scripts')
from constraint_parser import ConstraintParser

parser = ConstraintParser()
result = parser.parse('workspace/input/schedule_requirements.md')
# result: {
#   "teachers": [...],
#   "courses": [...],
#   "classrooms": [...],
#   "time_slots": [...],
#   "constraints": {
#     "hard": [...],
#     "soft": [...]
#   }
# }
```

```bash
python SKILLS/constraint-parser/scripts/constraint_parser.py <input_md_path> [--output <output_json_path>]
```

## 方法参考

| 方法 | 说明 |
|------|------|
| `parse(md_path)` | 解析单个 MD 文件，返回结构化约束 |
| `parse_batch(input_dir)` | 批量解析目录下所有 MD 文件 |
| `extract_teachers(text)` | 提取教师信息 |
| `extract_courses(text)` | 提取课程信息 |
| `extract_classrooms(text)` | 提取教室信息 |
| `extract_time_slots(text)` | 提取时间槽信息 |
| `extract_constraints(text)` | 提取约束条件 |

## MD 文档格式规范

排课需求文档应包含以下部分（可选，按需提供）：

```markdown
# 排课需求

## 教师信息
| 教师姓名 | 可用时间 | 偏好 | 备注 |
|----------|----------|------|------|
| 张老师 | 周一1-2节, 周三3-4节 | 上午优先 | 数学组 |
| 李老师 | 周二全天, 周四1-4节 | 无 | 英语组 |

## 课程信息
| 课程名称 | 课时数 | 授课教师 | 班级 | 连排要求 |
|----------|--------|----------|------|----------|
| 高等数学 | 4 | 张老师 | 2024级1班 | 每次2节 |
| 大学英语 | 2 | 李老师 | 2024级1班 | 无 |

## 教室信息
| 教室编号 | 容量 | 类型 | 可用时间 |
|----------|------|------|----------|
| A101 | 60 | 多媒体 | 全天 |
| B201 | 40 | 实验室 | 周一至周五 |

## 约束条件

### 硬约束（必须满足）
1. 同一教师同一时间不能上多门课
2. 同一班级同一时间不能上多门课
3. 课程必须在可用教室中进行

### 软约束（尽量满足）
1. 张老师 prefer 上午上课
2. 数学课尽量安排在上午
3. 同一门课的多次排课尽量间隔一天
```

## 输出 JSON 结构

```json
{
  "source_file": "schedule_requirements.md",
  "generated_at": "2026-06-09T12:00:00",
  "teachers": [
    {
      "id": "teacher_001",
      "name": "张老师",
      "available_slots": ["Mon-1", "Mon-2", "Wed-3", "Wed-4"],
      "preferences": {"period": "morning"},
      "group": "数学组"
    }
  ],
  "courses": [
    {
      "id": "course_001",
      "name": "高等数学",
      "hours_per_week": 4,
      "teacher_id": "teacher_001",
      "class_id": "class_001",
      "consecutive": 2
    }
  ],
  "classrooms": [
    {
      "id": "room_001",
      "name": "A101",
      "capacity": 60,
      "type": "multimedia",
      "available_slots": ["all"]
    }
  ],
  "classes": [
    {
      "id": "class_001",
      "name": "2024级1班",
      "size": 45
    }
  ],
  "time_slots": [
    {"id": "Mon-1", "day": "Monday", "period": 1, "time": "08:00-08:45"},
    {"id": "Mon-2", "day": "Monday", "period": 2, "time": "08:55-09:40"}
  ],
  "constraints": {
    "hard": [
      {"type": "no_teacher_conflict", "description": "同一教师同一时间不能上多门课"},
      {"type": "no_class_conflict", "description": "同一班级同一时间不能上多门课"},
      {"type": "room_capacity", "description": "教室容量必须大于班级人数"}
    ],
    "soft": [
      {"type": "teacher_preference", "teacher_id": "teacher_001", "preference": "morning", "weight": 0.8},
      {"type": "course_distribution", "course_id": "course_001", "min_gap_days": 1, "weight": 0.5}
    ]
  }
}
```

## 错误处理

- 输入文件不存在 → 返回错误信息
- MD 格式不规范 → 尝试尽可能解析，记录警告
- 信息缺失 → 使用默认值或标记为待确认
