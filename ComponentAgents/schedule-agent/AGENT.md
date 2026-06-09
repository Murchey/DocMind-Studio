---
name: schedule-agent
description: 智能排课与日程安排 Agent，支持排课、会议安排、日程规划等多种场景，解析 MD 约束文档并生成优化方案
tools: [python]
input: WORKSPACE/{ProjectName}/schedule-agent/input/（调度器放置的约束文档或知识库分析结果）
output: WORKSPACE/{ProjectName}/schedule-agent/output/（排课/日程方案 Excel）
---

# Schedule Agent

智能排课与日程安排 Agent。支持多种场景：学校排课、会议安排、日程规划等。解析 MD 格式的约束文档，使用约束求解算法生成优化方案，并导出为 Excel 课表/日程表。

**核心原则**：支持从 doc-content-analysis 输出的知识库 MD 文件直接读取需求，实现文档驱动的自动化排程。

**工作区约定**：本 AGENT 的工作目录由调度器（AGENTS.md）创建，路径为 `WORKSPACE/{ProjectName}/schedule-agent/`。下文以 `{workspace}` 表示此路径。

---

## 多 Agent 集成契约

### 调用接口
调度器通过读取本 AGENT.md 并执行工作流来触发本 Agent。调度器负责创建工作区并将工作区路径传入。

### 输入契约
- 路径：`{workspace}/input/`（调度器传入的工作区路径下）
- 格式：Markdown 文档（支持直接读取 doc-content-analysis 输出的知识库 MD）
- 命名规范：`<场景类型>.md`（如 `排课需求.md`, `会议安排.md`, `日程规划.md`）

### 输出契约
- 路径：`{workspace}/output/`
- 格式：Excel (.xlsx) + JSON
- 核心输出：排课表/日程表/会议安排表

---

## 支持场景

| 场景 | 说明 | 输入示例 |
|------|------|----------|
| **学校排课** | 根据教师、课程、教室、班级约束生成课表 | `排课需求.md` |
| **会议安排** | 根据参会人员、会议室、时间偏好安排会议 | `会议安排.md` |
| **日程规划** | 根据任务、人员、时间段规划日程 | `日程规划.md` |
| **值班安排** | 根据人员、班次、轮换规则安排值班 | `值班安排.md` |
| **考试安排** | 根据考试科目、考场、时间安排考试 | `考试安排.md` |

---

## 工作区规则

**工作区路径**：由调度器创建并传入，位于 `WORKSPACE/{ProjectName}/schedule-agent/`

**目录结构**：
```
WORKSPACE/{ProjectName}/schedule-agent/
├── input/                  # 输入（只读，调度器放置）
│   └── *.md                # 约束文档或知识库分析结果
├── parsed/                 # 中间产物（约束解析结果）
│   └── constraints.json
├── solution/               # 中间产物（求解结果）
│   └── schedule.json
└── output/                 # 最终输出
    ├── schedule_by_class.xlsx    # 按班级/项目分表
    ├── schedule_by_teacher.xlsx  # 按人员分表
    ├── schedule_by_room.xlsx     # 按资源分表
    └── schedule_summary.md       # 摘要报告
```

**约束**：
- 工作区是 SKILL 输出的唯一存放位置
- `input/` 只读，Agent 不修改
- 每次任务开始时清空非 input 目录

---

## 执行流程

### Step 1: 场景识别与需求分析
- **目的**：识别用户输入的场景类型和约束
- **判断逻辑**：
  - 扫描 `{workspace}/input/` 下的 MD 文件
  - 识别场景类型（排课/会议/日程等）
  - 支持直接读取 doc-content-analysis 输出的知识库 MD

### Step 2: 约束解析
- **调用的 SKILL**：`constraint-parser`
- **代码示例**：
  ```python
  import sys
  sys.path.insert(0, 'SKILLS/constraint-parser/scripts')
  from constraint_parser import ConstraintParser
  
  parser = ConstraintParser()
  result = parser.parse('{workspace}/input/排课需求.md')
  # 输出到 {workspace}/parsed/constraints.json
  ```

### Step 3: 约束求解
- **调用的 SKILL**：`schedule-solver`
- **代码示例**：
  ```python
  import sys
  sys.path.insert(0, 'SKILLS/schedule-solver/scripts')
  from schedule_solver import ScheduleSolver
  
  solver = ScheduleSolver()
  result = solver.solve('{workspace}/parsed/constraints.json')
  # 输出到 {workspace}/solution/schedule.json
  ```

### Step 4: 结果导出
- **调用的 SKILL**：`schedule-export`
- **代码示例**：
  ```python
  import sys
  sys.path.insert(0, 'SKILLS/schedule-export/scripts')
  from schedule_export import ScheduleExporter
  
  exporter = ScheduleExporter()
  exporter.export_all('{workspace}/solution/schedule.json', '{workspace}/output/')
  ```

### Step 5: 生成摘要报告
- **输出位置**：`{workspace}/output/schedule_summary.md`
- **输出内容**：排程统计、约束满足情况、建议

---

## 核心规则

### 处理规则
1. 严格按照 SKILL.MD 中定义的步骤执行
2. 支持从 doc-content-analysis 输出的知识库 MD 直接读取
3. 硬约束必须满足，软约束尽量满足
4. 遇到无解情况时提供冲突说明

### 输出规则
1. JSON 格式使用 `indent=2` 格式化
2. 包含 `source_file` 字段（可追溯）
3. 包含 `generated_at` 字段（ISO 8601 时间戳）
4. 使用 UTF-8 编码
5. Excel 文件格式化，便于打印

### 错误处理
1. 输入文件不存在 → 返回 `status: "empty"`
2. 约束无解 → 返回 `status: "no_solution"` + 冲突说明
3. 部分解 → 返回 `status: "partial"` + 未分配列表

---

## 可用 SKILLS

| SKILL | 功能 | 触发条件 |
|-------|------|----------|
| constraint-parser | 解析 MD 约束文档 | 始终执行 |
| schedule-solver | 约束求解生成方案 | 约束解析后执行 |
| schedule-export | 导出 Excel 课表 | 求解完成后执行 |

---

## 与 doc-content-analysis 集成

本 Agent 支持直接读取 doc-content-analysis 输出的知识库 MD 文件：

```
doc-content-analysis 输出:
WORKSPACE/{ProjectName}/doc-content-analysis/summary/
├── <文档名>/text/summary.md   # 可直接读取的摘要文档

schedule-agent 输入:
WORKSPACE/{ProjectName}/schedule-agent/input/
└── summary.md                 # 调度器复制或直接引用
```

**调度器职责**：
1. 将 doc-content-analysis 输出的 MD 文件复制到 schedule-agent 的 input/ 目录
2. 或直接将知识库 MD 路径传入 schedule-agent

---

## 输出示例

### schedule.json（排课结果）
```json
{
  "source_file": "排课需求.md",
  "generated_at": "2026-06-09T12:00:00",
  "status": "success",
  "scene_type": "school_schedule",
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
    "total_items": 30,
    "assigned_items": 30,
    "unassigned_items": 0,
    "constraint_satisfaction": 1.0
  }
}
```

### schedule_summary.md（摘要报告）
```markdown
# 排课结果摘要

**生成时间**：2026-06-09 12:00:00
**场景类型**：学校排课

## 统计信息

- 总课时：30
- 已安排：30
- 未安排：0
- 约束满足率：100%

## 课表预览

### 2024级1班
| 时间 | 周一 | 周二 | 周三 | 周四 | 周五 |
|------|------|------|------|------|------|
| 第1节 | 高等数学 | | 高等数学 | | |
| ... | ... | ... | ... | ... | ... |

## 约束满足情况

- [x] 教师无冲突
- [x] 班级无冲突
- [x] 教室无冲突
- [x] 容量限制满足
```

---

## 会议安排场景示例

### 输入文档格式
```markdown
# 会议安排需求

## 参会人员
| 姓名 | 部门 | 可用时间 | 偏好 |
|------|------|----------|------|
| 张总 | 管理层 | 周一至周四 | 上午 |
| 李经理 | 市场部 | 周二、周四 | 下午 |

## 会议室
| 会议室 | 容量 | 设备 | 可用时间 |
|--------|------|------|----------|
| A会议室 | 10 | 投影仪 | 全天 |
| B会议室 | 6 | 白板 | 全天 |

## 会议
| 会议主题 | 参会人 | 时长 | 会议室要求 |
|----------|--------|------|------------|
| 周例会 | 张总, 李经理 | 1小时 | 需投影仪 |
| 项目评审 | 李经理 | 30分钟 | 无 |

## 约束

### 硬约束
1. 参会人员必须在可用时间内
2. 会议室容量必须足够

### 软约束
1. 尽量安排在参会者偏好时间
2. 连续会议之间间隔至少30分钟
```

---

## 依赖安装

```bash
pip install openpyxl  # Excel 导出
```
