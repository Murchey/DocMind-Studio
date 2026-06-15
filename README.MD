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
- **Structured Knowledge Base**: Build searchable, linkable knowledge repositories with JSON indexes
- **Workflow Engine**: Pre-built workflows for academic, enterprise, and custom scenarios
- **Agent System**: Modular agents for specific tasks (document analysis, Excel processing, PPT generation)
- **Incremental Updates**: Support iterative refinement without starting from scratch
- **Multiple Output Formats**: Generate DOCX, PPTX, Excel, Markdown, HTML outputs

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      AGENTS.md (Dispatcher)                  │
│         Workspace init, Agent dispatch, Data passing          │
└─────────────────────────┬───────────────────────────────────┘
                          │
        ┌─────────────────┼─────────────────┐
        ▼                 ▼                 ▼
┌───────────────┐ ┌───────────────┐ ┌───────────────┐
│   Workflow    │ │   Workflow    │ │   Workflow    │
│ Knowledge     │ │  Academic     │ │  Enterprise   │
│   Builder     │ │    Docs       │ │    Docs       │
└───────┬───────┘ └───────┬───────┘ └───────┬───────┘
        │                 │                 │
        ▼                 ▼                 ▼
┌─────────────────────────────────────────────────────────────┐
│                    ComponentAgents                            │
│  doc-content │ doc-form │ excel │ ppt-deep │ ppt-master │ ...│
└─────────────────────────────────────────────────────────────┘
```

---

## Agents

| Agent | Purpose | Input | Output |
|-------|---------|-------|--------|
| `doc-content-analysis` | Document content extraction & analysis | DOC/DOCX/PDF | JSON + MD |
| `doc-form-master` | Document formatting & conversion | MD/DOCX | DOCX/PDF |
| `excel-master` | Excel processing & analysis | XLSX/XLS/CSV | XLSX |
| `ppt-deep-summary` | PPT content summarization | PPTX | JSON + MD + HTML |
| `ppt-master` | PPT generation from sources | PDF/DOCX/MD | PPTX |
| `ppt-continuation-tool` | Complete unfinished PPT | PPTX + DOCX | PPTX |
| `phd-research-agent` | Academic paper review | DOCX | Suggestions |

---

## Workflows

### KnowledgeBuilder
Transform multiple documents into a structured knowledge base with indexes, keywords, and cross-references.

**Trigger**: "knowledge base", "structured", "batch processing", "keyword extraction"

### AcademicDocs
Process academic papers with formatting, citation management, and thesis preparation.

**Trigger**: "paper", "academic", "thesis", "formatting"

### EnterpriseDocs
Analyze enterprise documents including meeting minutes, reports, and data tables.

**Trigger**: "report", "enterprise", "meeting minutes", "data analysis"

---

## Use Cases

### Academic / Coursework
- Receive scattered project materials from seniors
- Generate complete defense presentations and project reports
- Integrate incomplete course materials
- Handle frequent requirement changes with incremental updates

**Why DocMind?**
- Auto-organize scattered materials → Extract core information → Generate deliverables
- Support incremental updates when requirements change
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

## Project Value

### Why not use enterprise tools (DingTalk, WeCom, Feishu)?
Enterprise tools handle standard workflows well, but lack deep customization. DocMind excels at fine-grained, personalized requirements that enterprise software doesn't prioritize.

### Why not use AI chatbots (Gemini, ChatGPT, Qwen)?
These are conversation-oriented and single-file focused. DocMind builds growable multi-file knowledge bases, not one-off outputs. We leverage AI capabilities to produce better structured results.

### Why not use NotebookLM or AnythingLLM?
- **NotebookLM**: Great for personal knowledge, but weak at cross-file analysis for specific projects
- **AnythingLLM**: General-purpose; DocMind adds workflow configuration and SKILL extension for multi-scenario adaptation
- **Output difference**: DocMind produces usable DOCX and PPT files, not just text blocks

---

## Quick Start

### 1. Place your documents

```
WORKSPACE/{ProjectName}/
└── doc-content-analysis/
    └── input/
        ├── report1.docx
        ├── paper.pdf
        └── data.xlsx
```

### 2. Run via AGENTS.md

The dispatcher (AGENTS.md) will:
1. Create project workspace
2. Initialize progress tracking
3. Dispatch to appropriate agents
4. Pass data between agents
5. Collect final outputs

### 3. Get outputs

```
WORKSPACE/{ProjectName}/
├── doc-content-analysis/summary/   # Structured analysis
├── doc-form-master/output/         # Formatted documents
├── ppt-master/output/              # Generated presentations
└── knowledge-base/                 # Knowledge repository
```

---

## Workspace Structure

```
DocMind-Studio/
├── AGENTS.md              # Dispatcher entry point
├── ComponentAgents/       # Agent implementations (read-only)
├── Workflows/             # Workflow configurations
├── WORKSPACE/             # Project workspaces (isolated by project)
└── DevelopDocs/           # Development documentation
```

---

## VS Code Extension

A companion extension is planned for:
- Quick preview of generated outputs
- Workflow configuration management
- Progress monitoring
- Rapid workflow creation

---

## License

See [LICENSE](./LICENSE) for details.
