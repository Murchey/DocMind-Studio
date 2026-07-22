"""XML Inspector - main script for DOCX format compliance checking."""
import json
import sys
import re
from pathlib import Path
from datetime import datetime


class XmlInspector:
    """Inspect DOCX formatting by reading XML internals. Supports auto-fix."""
    
    def __init__(self, docx_path, rules_path=None, workspace_dir=None, auto_fix=False, max_fix_rounds=3):
        self.docx_path = Path(docx_path)
        self.workspace_dir = Path(workspace_dir) if workspace_dir else Path("workspace")
        self.rules_path = rules_path
        self.auto_fix = auto_fix
        self.max_fix_rounds = max_fix_rounds
        self.fix_history = []
    
    def run(self):
        """Execute full inspection pipeline. Auto-fix loop if enabled."""
        report = self._inspect(self.docx_path)
        
        # Auto-fix loop
        if self.auto_fix and report["overall_grade"] not in ("A", "A-"):
            for round_num in range(1, self.max_fix_rounds + 1):
                print(f"\n[Auto-Fix] Round {round_num}/{self.max_fix_rounds}...")
                fix_report = self._apply_fixes(self.docx_path)
                if not fix_report.get("fixes"):
                    print("[Auto-Fix] No fixes applicable, stopping.")
                    break
                
                self.fix_history.append({
                    "round": round_num,
                    "fixes": fix_report["fixes"],
                    "output": fix_report.get("output_path", str(self.docx_path))
                })
                
                # Re-inspect
                report = self._inspect(self.docx_path)
                grade = report["overall_grade"]
                print(f"[Auto-Fix] After round {round_num}: grade={grade}, "
                      f"critical={report['summary']['critical']}, warnings={report['summary']['warnings']}")
                
                if grade in ("A", "A-"):
                    print("[Auto-Fix] Target grade reached, stopping.")
                    break
        
        # Add fix history to report
        report["fix_history"] = self.fix_history
        if self.fix_history:
            self._save_report(report)
        
        return report
    
    def _inspect(self, docx_path):
        """Run single inspection pass."""
        from docx_xml_reader import DocxXmlReader
        reader = DocxXmlReader(docx_path)
        doc_data = reader.read_document()
        
        from rule_engine import RuleEngine
        engine = RuleEngine(self.rules_path)
        issues = engine.check_all(doc_data)
        
        report = self._generate_report(doc_data, issues)
        self._save_report(report)
        self._print_summary(report)
        
        return report
    
    def _apply_fixes(self, docx_path):
        """Apply XML-level fixes to the DOCX file."""
        from docx_fixer import DocxFixer
        
        fixer = DocxFixer(docx_path, self.rules_path)
        fixes = fixer.fix(output_path=docx_path)
        
        return {
            "fixes": fixes,
            "output_path": str(docx_path),
            "fix_count": len(fixes)
        }
    
    def _generate_report(self, doc_data, issues):
        """Generate structured inspection report."""
        critical = [i for i in issues if i["severity"] == "critical"]
        warnings = [i for i in issues if i["severity"] == "warning"]
        suggestions = [i for i in issues if i["severity"] == "info"]
        
        # Compute grade
        if len(critical) > 5:
            grade = "D"
        elif len(critical) > 2:
            grade = "C"
        elif len(critical) > 0:
            grade = "B"
        elif len(warnings) > 5:
            grade = "B"
        elif len(warnings) > 0:
            grade = "A-"
        else:
            grade = "A"
        
        # Group issues by category
        by_category = {}
        for issue in issues:
            cat = issue["category"]
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append(issue)
        
        # Build report
        paragraphs = doc_data.get("paragraphs", [])
        non_empty = [p for p in paragraphs if not p.get("is_empty")]
        
        report = {
            "check_time": datetime.now().isoformat(),
            "source_file": str(self.docx_path),
            "overall_grade": grade,
            "summary": {
                "total_issues": len(issues),
                "critical": len(critical),
                "warnings": len(warnings),
                "suggestions": len(suggestions),
                "total_paragraphs": len(paragraphs),
                "non_empty_paragraphs": len(non_empty),
                "total_tables": len(doc_data.get("tables", [])),
                "estimated_pages": doc_data.get("estimated_pages", 0)
            },
            "critical_issues": critical,
            "warnings": warnings,
            "suggestions": suggestions,
            "by_category": {
                cat: {
                    "count": len(cat_issues),
                    "critical": len([i for i in cat_issues if i["severity"] == "critical"]),
                    "warnings": len([i for i in cat_issues if i["severity"] == "warning"])
                }
                for cat, cat_issues in by_category.items()
            },
            "document_info": {
                "page_size": doc_data.get("section", {}).get("page_size", {}),
                "margins": doc_data.get("section", {}).get("margins", {}),
                "style_count": len(set(
                    p.get("style_id", "") for p in paragraphs if p.get("style_id")
                )),
                "has_header": doc_data.get("section", {}).get("has_header", False),
                "has_footer": doc_data.get("section", {}).get("has_footer", False)
            }
        }
        
        return report
    
    def _save_report(self, report):
        """Save report to workspace."""
        report_dir = self.workspace_dir / "reports"
        report_dir.mkdir(parents=True, exist_ok=True)
        
        report_path = report_dir / "xml_inspection_report.json"
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        # Also save Markdown version
        md_path = report_dir / "xml_inspection_report.md"
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(self._to_markdown(report))
        
        print(f"[INFO] Report saved to {report_path}")
    
    def _to_markdown(self, report):
        """Convert report to Markdown."""
        lines = []
        lines.append("# DOCX 格式检查报告\n")
        lines.append(f"**文件**: {report['source_file']}")
        lines.append(f"**检查时间**: {report['check_time']}")
        lines.append(f"**综合评级**: **{report['overall_grade']}**\n")
        
        s = report['summary']
        lines.append("## 概要\n")
        lines.append(f"| 指标 | 数值 |")
        lines.append(f"|------|------|")
        lines.append(f"| 总问题数 | {s['total_issues']} |")
        lines.append(f"| 🔴 严重 | {s['critical']} |")
        lines.append(f"| 🟡 警告 | {s['warnings']} |")
        lines.append(f"| 🟢 建议 | {s['suggestions']} |")
        lines.append(f"| 段落数 | {s['total_paragraphs']} |")
        lines.append(f"| 表格数 | {s['total_tables']} |")
        lines.append(f"| 预估页数 | {s['estimated_pages']} |")
        
        if report['critical_issues']:
            lines.append("\n## 🔴 严重问题\n")
            for issue in report['critical_issues']:
                lines.append(f"- **{issue['category']}** ({issue['location']})")
                lines.append(f"  - 规则: {issue['rule']}")
                lines.append(f"  - 期望: {issue['expected']}")
                lines.append(f"  - 实际: {issue['actual']}")
                lines.append(f"  - 建议: {issue['suggestion']}")
        
        if report['warnings']:
            lines.append("\n## 🟡 警告\n")
            for issue in report['warnings']:
                lines.append(f"- **{issue['category']}** ({issue['location']})")
                lines.append(f"  - {issue['rule']}: {issue['suggestion']}")
        
        if report['suggestions']:
            lines.append("\n## 🟢 建议\n")
            for issue in report['suggestions']:
                lines.append(f"- {issue['rule']}: {issue['suggestion']}")
        
        lines.append("\n## 分类统计\n")
        for cat, info in report.get('by_category', {}).items():
            lines.append(f"- **{cat}**: {info['count']}个问题 (严重:{info['critical']}, 警告:{info['warnings']})")
        
        return "\n".join(lines)
    
    def _print_summary(self, report):
        """Print summary to console."""
        s = report['summary']
        grade = report['overall_grade']
        
        print(f"\n{'='*50}")
        print(f"DOCX 格式检查报告")
        print(f"{'='*50}")
        print(f"文件: {report['source_file']}")
        print(f"综合评级: {grade}")
        print(f"严重问题: {s['critical']} | 警告: {s['warnings']} | 建议: {s['suggestions']}")
        print(f"段落: {s['total_paragraphs']} | 表格: {s['total_tables']} | 预估页数: {s['estimated_pages']}")
        
        if report['critical_issues']:
            print(f"\n--- 严重问题 ---")
            for issue in report['critical_issues'][:5]:
                print(f"  [{issue['category']}] {issue['rule']}")
                print(f"    期望: {issue['expected']}  实际: {issue['actual']}")
                print(f"    位置: {issue['location']}")
            if len(report['critical_issues']) > 5:
                print(f"  ... 还有 {len(report['critical_issues'])-5} 个严重问题")
        
        print(f"{'='*50}\n")


if __name__ == "__main__":
    import sys
    
    docx_path = sys.argv[1] if len(sys.argv) > 1 else "workspace/input/input.docx"
    rules_path = sys.argv[2] if len(sys.argv) > 2 else None
    workspace_dir = sys.argv[3] if len(sys.argv) > 3 else None
    auto_fix = "--auto-fix" in sys.argv
    
    inspector = XmlInspector(docx_path, rules_path=rules_path, workspace_dir=workspace_dir, auto_fix=auto_fix)
    inspector.run()
