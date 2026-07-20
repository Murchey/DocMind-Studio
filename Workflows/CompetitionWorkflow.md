# 竞赛资源处理工作流

**目标**：处理竞赛资源包（ZIP/7Z），解析项目书和代码，自动生成答辩 PPT，并构建可成长式知识库。

---

## 工作流总览

```
竞赛资源包（ZIP/7Z）
    │
    ▼（调度器解压并放入 input/）
┌──────────────────────────────────────────────┐
│  Step 0: 工作区初始化                           │
│  创建 WORKSPACE/{ProjectName}/ 及 Agent 子目录   │
└──────────────────┬───────────────────────────┘
                   │
                   ▼
┌──────────────────────────────────────────────┐
│  Step 1: 竞赛资源解压与解析（预处理）            │
│  解压 ZIP/7Z，提取项目书、代码、文档             │
└──────────────────┬───────────────────────────┘
                   │
                   ▼
┌──────────────────────────────────────────────┐
│  Step 2: doc-content-analysis                 │
│  ┌─────────────────────────────────────────┐  │
│  │  1. doc-convertor：转换 + 内容/图片提取    │  │
│  │  2. AI 总结：生成 summary.json + summary.md│  │
│  │  3. 输出：manifest.json + content_hash    │  │
│  └─────────────────────────────────────────┘  │
│  输出：{workspace}/summary/manifest.json       │
└──────────────────┬───────────────────────────┘
                   │
                   ▼ 读取 manifest.json
┌──────────────────────────────────────────────┐
│  Step 3: ppt-master（竞赛答辩 PPT 生成）        │
│  ┌─────────────────────────────────────────┐  │
│  │  1. 内容结构化：背景、方法、结果、创新点    │  │
│  │  2. 调用 ppt-master 生成结构化 PPT         │  │
│  └─────────────────────────────────────────┘  │
│  输出：WORKSPACE/{ProjectName}/ppt-master/output/│
└──────────────────┬───────────────────────────┘
                   │
                   ▼
┌──────────────────────────────────────────────┐
│  Step 4: KnowledgeBuilderWorkflow（知识库构建） │
│  保存所有竞赛材料到可成长式知识库               │
│  输出：knowledge-base/                         │
└──────────────────────────────────────────────┘
```

---

## 经典场景

### 场景A：竞赛资源包处理

**输入**：ZIP/7Z 资源包（含项目书、代码、说明文档）
**输出**：答辩 PPT + 知识库

### 场景B：项目书解析 + 答辩 PPT

**输入**：已完成的项目书 DOCX + 补充材料
**输出**：结构化答辩演示文稿

### 场景C：竞赛资料归档

**输入**：历年竞赛材料、参考文档
**输出**：可检索的知识库

---

## 详细流程

### Step 0: 工作区初始化

调度器创建项目工作区：

```
WORKSPACE/{ProjectName}/
├── doc-content-analysis/
│   ├── input/
│   └── summary/
├── ppt-master/
│   ├── input/
│   ├── projects/
│   └── output/
└── knowledge-base/
```

### Step 1: 竞赛资源解压与解析

**类型**：预处理（由调度器或外部脚本完成）
**输入**：用户上传的 ZIP/7Z 资源包
**输出**：`WORKSPACE/{ProjectName}/input/` 下的项目书、代码、文档

**说明**：
- 解压 ZIP/7Z 格式资源包
- 提取项目书（DOCX/PDF）、代码文件、说明文档到 `input/` 目录
- 此步骤由调度器或外部脚本完成，工作流从解压后的文件开始

### Step 2: 内容提取

**调用**：`doc-content-analysis`
**配置**：`ComponentAgents/doc-content-analysis/AGENT.md`
**Skill**：`doc-convertor` + `img-reader`（可选） + AI 总结

#### 输入

调度器将解压后的文档复制到：

```
WORKSPACE/{ProjectName}/doc-content-analysis/input/
├── 项目书.docx
├── 说明文档.pdf
└── 参考资料.txt
```

#### 执行

加载 `ComponentAgents/doc-content-analysis/AGENT.md`，按 Step 1 → Step 5b 执行：

1. **初始化工作区**：创建 `{workspace}/converted/` 和 `{workspace}/summary/`
2. **格式转换 + 内容提取**：`doc-convertor` Skill → `{workspace}/converted/` + `{workspace}/summary/*/text/content.json`
3. **图片提取**：`doc-convertor` Skill → `{workspace}/summary/*/img/`
4. **AI 总结**：AI 读取 content.json → 生成 `summary.json` + `summary.md`
5. **图片识别**（可选）：`img-reader` Skill → OCR + AI 视觉总结
6. **生成 manifest.json**：含 `content_hash`（每个 summary.json 的 SHA256）

#### 输出

```
{workspace}/summary/
├── manifest.json              # 处理清单（含 content_hash）
├── 项目书/
│   └── text/
│       ├── content.json       # 结构化文档内容
│       ├── summary.json       # 结构化索引
│       └── summary.md         # 可读总结
├── 说明文档/
│   └── text/
│       ├── content.json
│       ├── summary.json
│       └── summary.md
└── 综合总结.json/md           # 多文档综合总结
```

**关键字段**：
- `content_hash`：用于增量检测文档是否变更
- `summary_json`：下游 Agent 消费的入口文件

**独立调用点**：
- 调度器加载 `ComponentAgents/doc-content-analysis/AGENT.md` 按执行流程完成内容提取
- 最低层调用为 `doc-convertor` 和 `img-reader` 脚本，由 AGENT.md 编排
- 文档空时 manifest.json 的 status 为 "empty"，工作流应终止

### Step 3: 竞赛答辩 PPT 构建

**调用**：`ppt-master`
**配置**：`ComponentAgents/ppt-master/AGENT.md`
**输入**：Step-2 的提取结果 + 项目书核心内容
**输出**：`WORKSPACE/{ProjectName}/ppt-master/output/*.pptx`

#### 子步骤

1. **内容结构化**
   - 从项目书 summary.json 中提取：项目背景、研究方法、实验结果、创新点
   - 生成 PPT 大纲结构

2. **PPT 生成**
   - 调用 `ppt-master` 的 `SKILL.md` 流程
   - 生成结构化 PPT（封面、目录、背景、方法、结果、创新点、致谢）

#### 输出路径

```
WORKSPACE/{ProjectName}/ppt-master/
├── input/                     # 原始资料
├── projects/
│   └── <name>/
│       └── exports/           # 生成的 PPTX
└── output/                    # 调度器收集的最终输出
    └── *.pptx
```

**独立调用点**：
- 调度器加载 `ComponentAgents/ppt-master/AGENT.md` 按执行流程完成 PPT 生成
- ppt-master 是 AI Agent，通过 AGENT.md 定义的工作流调度其内部 SKILL 完成，非直接执行 SKILL.md 文件

### Step 4: 知识库构建

**调用**：`KnowledgeBuilderWorkflow`
**配置**：`Workflows/KnowledgeBuilderWorkflow.md`
**输入**：所有竞赛材料（项目书、代码、文档、PPT）
**输出**：`knowledge-base/`

**说明**：
- 调用 `kb_manager.py update` 进行增量构建
- 自动检测新增/变更/删除的文档
- 生成可成长式知识库索引

**执行命令**：
```bash
python ComponentAgents/doc-content-analysis/SKILLS/knowledge-builder/scripts/kb_manager.py update \
  knowledge-base/ \
  WORKSPACE/{ProjectName}/doc-content-analysis/summary/ \
  WORKSPACE/{ProjectName}/doc-content-analysis/summary/manifest.json
```

---

## 调度代码示例

```python
import shutil
import subprocess
from pathlib import Path

def execute_competition(project_name: str, zip_file: str = None):
    """执行 CompetitionWorkflow 工作流"""
    
    ws = Path(f"WORKSPACE/{project_name}")
    ws.mkdir(parents=True, exist_ok=True)
    
    # Step 0: 初始化 Agent 子目录
    for agent in ["doc-content-analysis", "ppt-master"]:
        (ws / agent / "input").mkdir(parents=True, exist_ok=True)
        (ws / agent / "output").mkdir(parents=True, exist_ok=True)
    
    # Step 1: 解压资源包（如提供）
    if zip_file and Path(zip_file).exists():
        input_dir = ws / "input"
        input_dir.mkdir(exist_ok=True)
        shutil.unpack_archive(zip_file, input_dir)
        
        # 将解压后的文档复制到 doc-content-analysis/input/
        for f in input_dir.rglob("*"):
            if f.is_file() and f.suffix.lower() in [".doc", ".docx", ".pdf", ".txt", ".md"]:
                shutil.copy2(f, ws / "doc-content-analysis" / "input" / f.name)
    
    # Step 2: 内容提取
    for doc in (ws / "doc-content-analysis" / "input").iterdir():
        if doc.is_file():
            subprocess.run([
                "python",
                "ComponentAgents/doc-content-analysis/SKILLS/doc-convertor/scripts/doc_converter.py",
                str(doc)
            ], check=True)
    
    # Step 3: PPT 生成
    # 1) 将 summary.md 复制到 ppt-master/input/
    summary_files = list((ws / "doc-content-analysis" / "summary").rglob("summary.md"))
    for sf in summary_files:
        shutil.copy2(sf, ws / "ppt-master" / "input" / f"doc_{sf.parent.name}.md")
    combined = ws / "doc-content-analysis" / "summary" / "综合总结.md"
    if combined.exists():
        shutil.copy2(combined, ws / "ppt-master" / "input" / "综合总结.md")
    
    # 2) 读取 ComponentAgents/ppt-master/AGENT.md 执行生成流程
    # 3) 将 projects/<name>/exports/ 中的 PPTX 复制到 ppt-master/output/
    
    # Step 4: 知识库构建
    manifest = ws / "doc-content-analysis" / "summary" / "manifest.json"
    if manifest.exists():
        import json
        with open(manifest, "r", encoding="utf-8") as f:
            data = json.load(f)
        if data.get("status") == "completed":
            subprocess.run([
                "python",
                "ComponentAgents/doc-content-analysis/SKILLS/knowledge-builder/scripts/kb_manager.py",
                "update",
                "knowledge-base/",
                str(ws / "doc-content-analysis" / "summary"),
                str(ws / "doc-content-analysis" / "summary" / "manifest.json")
            ], check=True)
    
    print(f"CompetitionWorkflow 执行完成，输出：")
    print(f"  - PPT: {ws / 'ppt-master' / 'output'}")
    print(f"  - 知识库: knowledge-base/")
```

---

## 独立 Agent 调用点汇总

| 场景 | 独立调用 Agent | 用途 |
|------|--------------|------|
| 解析项目书内容 | `doc-content-analysis` | 内容提取 + AI 总结 |
| 生成竞赛答辩 PPT | `ppt-master` | PPT 自动化生成 |
| 构建竞赛知识库 | `KnowledgeBuilderWorkflow` | 增量更新知识库 |

---

## 输出位置

| 路径 | 说明 |
|------|------|
| `WORKSPACE/{ProjectName}/doc-content-analysis/summary/` | 项目书/代码提取结果（manifest.json + summary） |
| `WORKSPACE/{ProjectName}/ppt-master/output/` | 答辩 PPT（PPTX） |
| `knowledge-base/` | 竞赛知识库（.kb_state.json + 索引） |

---

## 状态检查

| 条件 | 动作 |
|------|------|
| Step-2 manifest.json 中 `status == "completed"` | 继续 Step-3（PPT生成）和 Step-4（知识库构建） |
| Step-2 manifest.json 中 `status == "empty"` | 终止工作流，提示用户：无可处理的文档格式 |
| Step-2 manifest.json 中 `status == "failed"` | 终止工作流，读取错误原因并提示修正 |
| Step-3 PPT 生成完成 | 收集 PPTX 到 ppt-master/output/ |
| Step-4 知识库构建完成 | 输出最终产物清单 |

---

## 错误处理

| 场景 | 策略 | 说明 |
|------|------|------|
| manifest 状态不是 completed | 终止 | 文档内容提取未成功完成 |
| knowledge-base/ 不存在 | 降级 | 自动切换为 init 模式首次构建 |
| ppt-master 目录不存在 | 跳过 | 跳过 PPT 生成，继续知识库构建 |
| input/ 目录为空 | 终止 | 未找到可处理的文档 |
