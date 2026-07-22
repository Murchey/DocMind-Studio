# DocMind-Studio

> AI-Driven Multi-Document Summarization & Output Platform

[中文文档](./README_CN.MD)

---

## Overview

DocMind-Studio is an AI-powered platform for multi-document analysis, structured knowledge base construction, and automated output generation. Similar to Google NotebookLM but with multi-file knowledge base capabilities, it transforms scattered documents into structured, actionable outputs.

**Core Concept**: Transform multiple document sources (DOC, DOCX, PDF, PPT, Excel, TXT, MD) into structured knowledge bases and professional outputs (reports, presentations, formatted documents).

---

## Key Features

- **Multi-Document Processing**: Handle DOC, DOCX, PDF, PPTX, XLSX, TXT, MD files simultaneously
- **Structured Knowledge Base**: Build searchable, linkable knowledge repositories with JSON indexes, supporting incremental updates and cross-agent registration
- **Workflow Engine**: Pre-built workflows for academic, enterprise, competition, and knowledge base scenarios
- **Agent System**: Modular agents for specific tasks (document analysis, formatting, Excel processing, PPT generation, research assistance)
- **AI Format Compliance**: Auto-parse DOCX XML structure to check and fix formatting issues (fonts, line spacing, margins, three-line tables, etc.)
- **Progress Visualization**: ProgressTracker for real-time task progress with plugin Dashboard integration
- **Multiple Output Formats**: Generate DOCX, PPTX, Excel, Markdown, HTML outputs

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    AGENTS.md (Dispatcher)                        │
│    Workspace init · ProgressTracker · Agent dispatch             │
└──────────────────────────┬──────────────────────────────────────┘
                           │
     ┌──────────┬──────────┼──────────┬──────────┐
     ▼          ▼          ▼          ▼          ▼
┌─────────┐┌─────────┐┌─────────┐┌─────────┐┌─────────┐
│Knowledge││Academic ││Enter-   ││Competi- ││  PPT    │
│ Builder ││  Docs   ││prise    ││tion     ││Continue │
└────┬────┘└────┬────┘└────┬────┘└────┬────┘└────┬────┘
     │          │          │          │          │
     ▼          ▼          ▼          ▼          ▼
┌─────────────────────────────────────────────────────────────────┐
│                    ComponentAgents                                │
│ doc-content │ doc-form │ excel │ ppt-deep │ ppt-master │ phd-re │
│             │ +AI chk  │       │          │            │ search │
└─────────────────────────────────────────────────────────────────┘
```

---

## Agents

| Agent | Purpose | Input | Output |
|-------|---------|-------|--------|
| `doc-content-analysis` | Document content extraction & analysis | DOC/DOCX/PDF | JSON + MD |
| `doc-form-master` | Document formatting with AI format check & auto-fix | MD/DOCX | DOCX/PDF |
| `excel-master` | Excel processing & analysis | XLSX/XLS/CSV | XLSX |
| `ppt-deep-summary` | PPT content summarization | PPTX | JSON + MD + HTML |
| `ppt-master` | PPT generation from sources | PDF/DOCX/MD | PPTX |
| `ppt-continuation-tool` | Complete unfinished PPT | PPTX + DOCX | PPTX |
| `phd-research-agent` | Research assistance (review/proposal/intro drafting) | DOCX | Suggestions |

---

## Workflows

### KnowledgeBuilder
Transform multiple documents into a structured knowledge base with indexes, keywords, and cross-references. Supports incremental updates and cross-agent registration.

**Trigger**: "knowledge base", "structured", "batch processing", "keyword extraction"

### AcademicDocs
Process academic papers including content extraction, review, Introduction drafting, proposal generation, and formatted output.

**Trigger**: "paper", "academic", "review", "proposal", "formatting"

### EnterpriseDocs
Analyze enterprise documents including meeting minutes, reports, data table comparison, and presentation generation.

**Trigger**: "report", "enterprise", "meeting minutes", "data analysis"

### Competition
Process competition resource packages, extract project core points, and generate concise defense presentations.

**Trigger**: "competition", "defense", "challenge cup", "project proposal"

---

## Use Cases

### Academic / Coursework
- Receive scattered project materials from seniors
- Generate complete defense presentations and project reports
- Integrate incomplete course materials
- Handle frequent requirement changes with incremental updates
- **Research assistance**: idea evaluation, paper review, Introduction drafting, proposal generation
- **AI format check**: Auto-detect and fix fonts, line spacing, margins, three-line tables

**Why DocMind?**
- Auto-organize scattered materials → Extract core information → Generate deliverables
- Support incremental updates when requirements change
- AI format check ensures academic standards compliance without manual verification
- Save manual compilation time

**When it's indispensable**: 20+ documents need to become presentable defense materials overnight.

### Enterprise / Business
- Consolidate project tables, meeting minutes, and schedules
- Compare and summarize multiple data sources
- Generate reports, presentations, and planning documents

**Why DocMind?**
- Excel Master + Doc/PPT Master automate comparison and summarization
- Knowledge Builder maintains growing knowledge assets
- Avoid repetitive manual operations

**When it's indispensable**: 10+ tables and multiple meeting minutes need quick report generation.

---

## Why DocMind?

### vs Enterprise Tools (DingTalk, Feishu, etc.)
Enterprise tools handle standard workflows well, but fall short on custom needs like "format 20 papers to a single academic standard." DocMind is built for exactly these fine-grained, personalized document tasks.

### vs AI Chatbots (ChatGPT, Qwen, etc.)
AI chatbots are one-off — conversation ends, output is gone. DocMind builds a **growable knowledge base**. Your document assets accumulate over time and can be reused across projects.

### vs NotebookLM / AnythingLLM
NotebookLM is great for personal knowledge management, but outputs text, not usable files. DocMind outputs **formatted DOCX papers** and **presentable PPT files** — ready to use.

---

## Tech Highlights

### AI Format Compliance Checker (format-ai-checker)
- **How it works**: Unzip DOCX as a ZIP archive, read internal XML structure (`word/document.xml`, `word/styles.xml`), parse every formatting attribute precisely
- **Checks**: Page size/margins, fonts, paragraph alignment/line spacing/indentation, heading hierarchy, three-line table spec, document structure
- **Auto-fix**: Automatically modify XML attributes when issues are found, re-verify up to 3 rounds
- **Zero dependencies**: No PDF conversion or vision models — pure XML parsing, fast and precise

### Knowledge Base Incremental Updates
- Fingerprint comparison via `content_hash` — only processes new/changed/deleted documents
- Cross-agent registration — multiple agents can contribute summaries to a single project knowledge base

---

## Quick Start

### Step 1: Tell us what you need

Describe your requirement in natural language, for example:

- "Help me turn these papers into a thesis proposal" → **Academic workflow**
- "Here's our competition resource pack, generate a defense PPT" → **Competition workflow**
- "Format this paper to academic standards" → **Formatting + AI check**
- "Compare data across these spreadsheets" → **Excel processing**
- "Build a knowledge base from these documents" → **Knowledge base**

### Step 2: Provide your documents

Place your files in the `input/` directory. The system creates the directory structure automatically:

```
WORKSPACE/{your-project}/
└── doc-content-analysis/
    └── input/
        ├── paper1.pdf
        ├── report.docx
        └── data.xlsx
```

> You don't need to create directories manually — the dispatcher handles it.

### Step 3: Wait and monitor progress

The dispatcher orchestrates the entire workflow. Track progress in real time via the **VS Code Dashboard**:

- Content extraction complete → auto-advances to next step
- Formatting done → AI format check triggers automatically, fixes issues on the spot
- All steps complete → you're notified

### Step 4: Get your results

Pick up your deliverables from the output directories:

```
WORKSPACE/{your-project}/
├── doc-form-master/output/         # Formatted paper (DOCX)
├── ppt-master/output/              # Defense presentation (PPTX)
├── excel-master/output/            # Comparison analysis
├── doc-content-analysis/summary/   # Structured analysis report
└── knowledge-base/                 # Project knowledge base (queryable)
```

### Examples

**Example 1: Academic paper formatting**
```
You: Help me format this paper to academic standards
     → Provide the DOCX file
System: Auto-format → AI checks 20+ rules → Auto-fixes issues → Outputs compliant DOCX
```

**Example 2: Competition defense PPT**
```
You: Here are our Challenge Cup project materials, make a defense PPT
     → Provide a ZIP resource pack
System: Extract & analyze → Pull core points → Generate concise defense PPT + knowledge base
```

**Example 3: Multi-table comparison**
```
You: Compare differences across these course schedules
     → Provide multiple Excel files
System: Auto-detect headers → Generate diff report + visual charts
```

---

## Project Structure

```
DocMind-Studio/
├── AGENTS.md              # Dispatcher (auto-orchestrates workflows)
├── ComponentAgents/       # Agent modules (each handles a task)
├── Workflows/             # Workflow configurations
├── WORKSPACE/             # Project workspaces (isolated per project)
└── DevelopDocs/           # Development docs
```

---

## VS Code Extension

Companion VS Code extension:
- **Progress monitoring**: Real-time task progress tracking (implemented)
- **Quick preview**: One-click preview of generated documents and PPTs
- **Workflow management**: Configure and switch between workflows

---

## Open Source Dependencies

This project builds upon the following open-source projects. Special thanks to their authors:

| Component | Author | License | Repository |
|-----------|--------|---------|------------|
| ppt-master | [Hugo He](https://github.com/hugohe3) | MIT | [hugohe3/ppt-master](https://github.com/hugohe3/ppt-master) |
| phd-research-agent | [HKUSTDial](https://github.com/HKUSTDial) | CC BY-NC-SA 4.0 | [HKUSTDial/Supervisor-Skills](https://github.com/HKUSTDial/Supervisor-Skills) |

> phd-research-agent is adapted from Supervisor-Skills under the CC BY-NC-SA 4.0 license (free to share and adapt for non-commercial use, with attribution).

---

## License

See [LICENSE](./LICENSE) for details.
