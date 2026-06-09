---
name: ppt-continuation-tool
description: 接收外部半完成的 PPTX 和相关 DOCX 资料，分析已完成内容，继续生成剩余页面并输出完整 PPTX。
tools: [python]
input: WORKSPACE/{ProjectName}/ppt-continuation-tool/input/（外部半完成 .pptx + .docx 资料）
output: WORKSPACE/{ProjectName}/ppt-continuation-tool/output/（继续完成的 .pptx）
---

# PPT Continuation Tool

接收外部半完成的 PPTX 和相关 DOCX 资料，分析已完成内容，继续生成剩余页面并输出完整 PPTX。

**核心原则**：保留外部 PPT 已完成页面的设计和内容，基于 DOCX 资料补充缺失页面，保持风格统一。

**工作区约定**：本 AGENT 的工作目录由调度器（AGENTS.md）创建，路径为 `WORKSPACE/{ProjectName}/ppt-continuation-tool/`。下文以 `{workspace}` 表示此路径。

---

## 多 Agent 集成契约

### 调用接口
调度器通过读取本 AGENT.md 并执行工作流来触发本 Agent。调度器负责创建工作区并将工作区路径传入。

### 输入契约
- 路径：`{workspace}/input/`
- 格式：`.pptx`（外部半完成 PPT）+ `.docx`（参考资料）
- 命名规范：主 PPT 文件名含 `ppt` 或 `演示`，资料文件名含 `资料`、`参考`、`内容` 等

### 输出契约
- 路径：`{workspace}/output/`
- 格式：`.pptx`（继续完成的完整 PPT）
- 核心输出：`{workspace}/output/<项目名>_completed_<时间戳>.pptx`

---

## 工作区规则

**工作区路径**：由调度器创建并传入，位于 `WORKSPACE/{ProjectName}/ppt-continuation-tool/`

**目录结构**：
```
WORKSPACE/{ProjectName}/ppt-continuation-tool/
├── input/                  # 输入（只读，调度器放置）
│   ├── *.pptx             # 外部半完成 PPT
│   └── *.docx             # 参考资料
├── analysis/              # 分析结果
│   ├── slide_library.json # 幻灯片库分析
│   ├── completion_plan.json # 续写计划
│   └── check_report.json  # 容量检查报告
├── sources/               # 转换后的源材料
│   └── *.md               # DOCX 转换的 Markdown
└── output/                # 最终输出
    └── *.pptx             # 继续完成的 PPTX
```

**约束**：
- 工作区是 SKILL 输出的唯一存放位置
- `input/` 只读，Agent 不修改
- 每次任务开始时清空非 input 目录

---

## 执行流程

### Step 1: 源材料转换
- **目的**：将 DOCX 参考资料转换为 Markdown 格式
- **调用的 SKILL**：`continuation-analyzer`
- **代码示例**：
  ```python
  import sys
  sys.path.insert(0, 'ComponentAgents/ppt-continuation-tool/SKILLS/continuation-analyzer/scripts')
  from doc_to_md import convert_doc_to_md
  
  # 转换所有 DOCX 文件
  convert_doc_to_md('{workspace}/input/', '{workspace}/sources/')
  ```
- **输出位置**：`{workspace}/sources/`

### Step 2: PPT 分析
- **目的**：分析外部 PPT 的幻灯片结构，识别已完成和未完成页面
- **调用的 SKILL**：`continuation-analyzer`
- **代码示例**：
  ```python
  import sys
  sys.path.insert(0, 'ComponentAgents/ppt-continuation-tool/SKILLS/continuation-analyzer/scripts')
  from ppt_analyzer import analyze_ppt
  
  result = analyze_ppt(
      pptx_path='{workspace}/input/*.pptx',
      output_path='{workspace}/analysis/slide_library.json'
  )
  ```
- **输出位置**：`{workspace}/analysis/slide_library.json`

### Step 3: 续写计划生成
- **目的**：基于 PPT 分析和 DOCX 内容，生成续写计划
- **调用的 SKILL**：`continuation-analyzer`
- **处理逻辑**：
  1. 读取 `slide_library.json` 了解已有幻灯片
  2. 读取 `sources/*.md` 获取参考资料内容
  3. 识别缺失章节（如：无封面、无目录、无结尾等）
  4. 生成 `completion_plan.json`，定义需要新增的幻灯片
- **输出位置**：`{workspace}/analysis/completion_plan.json`

### Step 4: 容量检查
- **目的**：检查续写计划中的文本是否适合目标幻灯片布局
- **调用的 SKILL**：`continuation-filler`
- **代码示例**：
  ```python
  import sys
  sys.path.insert(0, 'ComponentAgents/ppt-continuation-tool/SKILLS/continuation-filler/scripts')
  from capacity_checker import check_capacity
  
  report = check_capacity(
      slide_library='{workspace}/analysis/slide_library.json',
      fill_plan='{workspace}/analysis/completion_plan.json',
      output_path='{workspace}/analysis/check_report.json'
  )
  ```
- **输出位置**：`{workspace}/analysis/check_report.json`

### Step 5: 执行续写
- **目的**：根据计划生成新幻灯片并合并到原 PPT
- **调用的 SKILL**：`continuation-filler`
- **代码示例**：
  ```python
  import sys
  sys.path.insert(0, 'ComponentAgents/ppt-continuation-tool/SKILLS/continuation-filler/scripts')
  from ppt_filler import execute_fill
  
  result = execute_fill(
      source_pptx='{workspace}/input/*.pptx',
      fill_plan='{workspace}/analysis/completion_plan.json',
      output_path='{workspace}/output/'
  )
  ```
- **输出位置**：`{workspace}/output/`

### Step 6: 生成 manifest.json
- **目的**：生成处理清单供调度器消费
- **输出位置**：`{workspace}/output/manifest.json`

---

## 核心规则

### 处理规则
1. 严格按照 SKILL.MD 中定义的步骤执行
2. 保留外部 PPT 已完成页面的原始设计
3. 新增页面风格与已有页面保持一致
4. 所有内容必须来源于 DOCX 参考资料

### 输出规则
1. JSON 格式使用 `indent=2` 格式化
2. 包含 `source_file` 字段（可追溯）
3. 包含 `generated_at` 字段（ISO 8601 时间戳）
4. 使用 UTF-8 编码

### 错误处理
1. 输入文件不存在 → 返回 `status: "empty"`
2. PPT 格式损坏 → 返回 `status: "failed"` + 错误信息
3. DOCX 转换失败 → 跳过该文件，继续处理其他文件

---

## 可用 SKILLS

| SKILL | 功能 | 触发条件 |
|-------|------|----------|
| continuation-analyzer | 分析外部 PPT 结构，识别已完成/未完成页面 | Step 1-3 |
| continuation-filler | 执行续写计划，生成新幻灯片 | Step 4-5 |

---

## 输出示例

### manifest.json
```json
{
  "status": "completed",
  "total_slides": 15,
  "original_slides": 8,
  "new_slides": 7,
  "source_files": ["input.pptx", "资料.docx"],
  "output_file": "{workspace}/output/项目名_completed_20260609_120000.pptx",
  "generated_at": "2026-06-09T12:00:00"
}
```
