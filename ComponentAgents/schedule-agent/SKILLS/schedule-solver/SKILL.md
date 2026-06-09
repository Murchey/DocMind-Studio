---
name: schedule-solver
description: 排课约束求解器，使用回溯算法和启发式策略生成满足所有硬约束的排课方案
tools: [python]
---

# Schedule Solver

排课约束求解器，基于约束满足问题（CSP）算法，生成满足所有硬约束并尽量满足软约束的排课方案。

## 功能说明

- 解析结构化约束数据（JSON）
- 使用回溯算法 + 启发式策略求解
- 支持硬约束（必须满足）和软约束（尽量满足）
- 输出排课结果（JSON）

## 输入/输出

**输入**：
- `workspace/parsed/constraints.json`：结构化约束数据（由 constraint-parser 生成）

**输出**：
- `workspace/solution/schedule.json`：排课结果
- `workspace/solution/schedule_summary.md`：排课摘要（人类可读）

## 调用方式

```python
import sys
sys.path.insert(0, 'SKILLS/schedule-solver/scripts')
from schedule_solver import ScheduleSolver

solver = ScheduleSolver()
result = solver.solve('workspace/parsed/constraints.json')
# result: {
#   "status": "success",
#   "assignments": [...],
#   "statistics": {...}
# }
```

```bash
python SKILLS/schedule-solver/scripts/schedule_solver.py <constraints_json_path> [--output <output_json_path>]
```

## 方法参考

| 方法 | 说明 |
|------|------|
| `solve(constraints_path)` | 求解排课问题，返回排课结果 |
| `solve_from_dict(constraints)` | 从字典对象求解 |
| `validate_schedule(schedule, constraints)` | 验证排课方案是否满足约束 |
| `get_statistics(schedule)` | 获取排课统计信息 |

## 算法说明

### 1. 变量和域定义

- **变量**：每门课程的每个课时
- **域**：可用的（时间槽，教室）组合

### 2. 约束传播

- **硬约束**：
  - 教师冲突：同一教师同一时间只能上一门课
  - 班级冲突：同一班级同一时间只能上一门课
  - 教室冲突：同一教室同一时间只能安排一门课
  - 容量限制：教室容量 >= 班级人数
  - 教师可用性：课程必须在教师可用时间内

- **软约束**：
  - 教师偏好：尽量满足教师的时间偏好
  - 课程分布：同一门课的多次排课尽量分散
  - 连排要求：需要连排的课程安排在连续时间槽

### 3. 求解策略

1. **最小剩余值（MRV）**：优先安排可选时间最少的课程
2. **度启发式**：当 MRV 相同时，优先安排约束最多的课程
3. **前向检查**：每次赋值后检查后续变量的域是否为空
4. **回溯**：当无法继续时回溯到上一步

## 输出 JSON 结构

```json
{
  "source_file": "constraints.json",
  "generated_at": "2026-06-09T12:00:00",
  "status": "success",
  "assignments": [
    {
      "course_id": "course_001",
      "course_name": "高等数学",
      "teacher_id": "teacher_001",
      "teacher_name": "张老师",
      "class_id": "class_001",
      "class_name": "2024级1班",
      "room_id": "room_001",
      "room_name": "A101",
      "time_slot_id": "Mon-1",
      "day": "Monday",
      "period": 1,
      "time": "08:00-08:45"
    }
  ],
  "statistics": {
    "total_courses": 10,
    "total_hours": 30,
    "assigned_hours": 30,
    "unassigned_hours": 0,
    "hard_constraint_violations": 0,
    "soft_constraint_score": 0.85,
    "teacher_satisfaction": {
      "teacher_001": 0.9,
      "teacher_002": 0.8
    }
  },
  "unassigned": [],
  "warnings": []
}
```

## 错误处理

- 约束无解 → 返回 `status: "no_solution"` 和冲突说明
- 部分解 → 返回 `status: "partial"` 和未分配列表
- 输入格式错误 → 返回错误信息
