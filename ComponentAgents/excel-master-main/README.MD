# Excel-Master

<p align="center">
  <strong>AI-Powered Excel Processing Assistant</strong>
</p>

<p align="center">
  <a href="./README.md">English</a> | <a href="./README_CN.md">中文</a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.9+-blue.svg" alt="Python 3.9+">
  <img src="https://img.shields.io/badge/License-GPL%203.0-green.svg" alt="License: GPL 3.0">
  <img src="https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey.svg" alt="Platform">
</p>

---

## Why Excel-Master?

**Tired of manual Excel processing?** Excel-Master is an AI assistant that automates batch processing, data analysis, table comparison, and report generation for Excel files.

### Key Benefits

- **Zero Learning Curve** - Just describe what you need in natural language
- **Visual Confirmation** - Web interface for reviewing data before processing
- **Batch Processing** - Handle hundreds of files simultaneously
- **Smart Comparison** - Automatically match and compare files with different naming
- **Data Visualization** - Generate charts and reports automatically

---

## Quick Start

### 1. Install Dependencies

```bash
# Windows
install_requirements.bat

# macOS/Linux
pip install -r requirements.txt
```

### 2. Start Using

Simply tell the AI Agent what you need:

```
"Compare the fee records in folder A with folder B"
"Filter students with grades above 80"
"Merge all class rosters into one file"
```

The Agent will guide you through the process with a visual web interface.

---

## Use Cases

### For Schools
- Compare fee collection records across classes
- Generate student performance reports
- Merge attendance sheets from multiple teachers

### For Businesses
- Reconcile financial records
- Consolidate department reports
- Analyze sales data trends

### For Any Organization
- Batch process standardized forms
- Compare before/after data changes
- Generate summary statistics

---

## Features

| Feature | Description |
|---------|-------------|
| **Batch Processing** | Process hundreds of Excel/CSV files at once |
| **Smart Comparison** | Compare files with automatic column matching |
| **Data Profiling** | Analyze data structure and quality |
| **Visual Preview** | Web interface for reviewing changes |
| **Chart Generation** | Create bar, line, pie, and scatter charts |
| **Format Conversion** | Convert .xls to .xlsx automatically |
| **Name Matching** | Match files with different naming conventions |

---

## How It Works

```
┌─────────────────────────────────────────────────────────────┐
│  1. Upload Files    →    2. AI Analyzes    →    3. Review   │
│     (Excel/CSV)         (Data Profiling)       (Web UI)    │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  4. Confirm Rules   →    5. Process    →    6. Download     │
│     (Visual Config)       (Automated)       (Results)       │
└─────────────────────────────────────────────────────────────┘
```

---

## Example Workflow

**Scenario**: Compare fee records between "Standard Charges" and "Actual Payments"

1. **Upload**: Place files in two folders
2. **Analyze**: AI detects file structures automatically
3. **Match**: System pairs files with similar names (e.g., "Class1.xlsx" ↔ "2.1.xlsx")
4. **Configure**: Web interface shows data preview, you select columns to compare
5. **Execute**: AI generates and runs comparison script
6. **Results**: Download detailed comparison report with differences highlighted

---

## Project Structure

```
Excel-Master/
├─ skills/                    # AI Skills
│  ├─ mkdir_workspace/        # Workspace creation
│  ├─ excel_io/               # Excel read/write
│  ├─ excel_scriptsGen/       # Custom script generation
│  ├─ excel_compare/          # Batch comparison
│  ├─ same_name_convertor/    # Smart file matching
│  ├─ data_profile/           # Data analysis
│  ├─ excel_compat/           # Format conversion
│  ├─ excel_chart/            # Chart generation
│  └─ excel_preview/          # Web preview interface
├─ workspace/                 # Auto-generated workspace
├─ requirements.txt           # Python dependencies
├─ AGENT.md                   # AI Agent workflow (English)
├─ AGENT_CN.md                # AI Agent workflow (Chinese)
└─ README.md                  # This file
```

---

## Deployment

### Prerequisites
- Python 3.9+
- pip (Python package manager)

### Installation

```bash
# Clone the repository
git clone https://github.com/your-username/excel-master.git
cd excel-master

# Install dependencies
pip install -r requirements.txt

# Or use the batch file (Windows)
install_requirements.bat
```

### Configuration

For AI capabilities, configure one of:
- **Trae CN** (Recommended for China)
- **Qwen Code**
- **Ollama** (Local deployment for privacy)

---

## Advanced Features

### Smart File Matching

When files have different names but same content:
- "二（1）班.xlsx" ↔ "2.1.xlsx"
- "Chapter1.xlsx" ↔ "第一章.xlsx"

The system automatically detects and matches them.

### Data Profiling

Before processing, the system analyzes:
- Column types and names
- Missing values
- Data distribution
- Sample values

### Visual Confirmation

Every operation requires user confirmation through a web interface:
- Preview data before processing
- Select specific columns
- Configure comparison rules
- Review results

---

## FAQ

**Q: Do I need to know Python?**
A: No! Just describe what you need in natural language.

**Q: Is my data secure?**
A: Yes! All processing happens locally. For extra privacy, use Ollama for local AI.

**Q: What file formats are supported?**
A: Excel (.xlsx, .xls) and CSV files.

**Q: Can I process hundreds of files?**
A: Yes! The system is designed for batch processing.

---

## Contributing

Contributions are welcome! Please read our contributing guidelines.

---

## License

This project is licensed under the GPL 3.0 License - see the [LICENSE](LICENSE) file for details.

---

## Support

- **Issues**: [GitHub Issues](https://github.com/your-username/excel-master/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-username/excel-master/discussions)

---

<p align="center">
  Made with ❤️ for educators, accountants, and data professionals
</p>