import json
from pathlib import Path
from datetime import datetime


class ReportGenerator:
    def __init__(self):
        self.reports_dir = Path("workspace/reports")
        self.reports_dir.mkdir(parents=True, exist_ok=True)

    def load_json_report(self, filename):
        filepath = self.reports_dir / filename
        if filepath.exists():
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def generate_summary_report(self):
        xml_report = self.load_json_report("xml_safety_report.json")
        formula_report = self.load_json_report("formula_report.json")
        font_report = self.load_json_report("font_report.json")
        fix_report = self.load_json_report("fix_report.json")
        pdf_report = self.load_json_report("pdf_export_report.json")

        summary = {
            "processing_date": datetime.now().isoformat(),
            "source_document": "《智能体平台应用》课程作业.docx",
            "document_type": "中文论文",
            "template_used": "chinese_academic.yaml",
            "processing_steps": [
                "DOCX解析",
                "XML安全验证",
                "数学公式保护",
                "模板加载",
                "字体兼容性验证",
                "格式标准化",
                "PDF导出"
            ],
            "xml_validation": {
                "xml_files_count": xml_report.get("xml_files", 0),
                "namespace_count": xml_report.get("namespace_count", 0),
                "relationship_count": xml_report.get("relationship_count", 0),
                "orphan_relationships": xml_report.get("orphan_relationships", 0),
                "xml_errors": xml_report.get("xml_errors", 0)
            },
            "formula_protection": {
                "total_formulas": formula_report.get("total_formulas", 0),
                "omml_formulas": formula_report.get("omml_formulas", 0),
                "inline_formulas": formula_report.get("inline_formulas", 0),
                "block_formulas": formula_report.get("block_formulas", 0)
            },
            "font_management": {
                "available_fonts_count": font_report.get("available_fonts_count", 0),
                "missing_fonts": font_report.get("missing_fonts", []),
                "fallback_mapping": font_report.get("fallback_mapping", {})
            },
            "format_normalization": {
                "paragraph_fixes": fix_report.get("paragraph_fixes", 0),
                "font_fixes": fix_report.get("font_fixes", 0),
                "heading_fixes": fix_report.get("heading_fixes", 0),
                "table_fixes": fix_report.get("table_fixes", 0)
            },
            "pdf_export": {
                "export_engine": pdf_report.get("export_engine", "Unknown"),
                "pdf_pages": pdf_report.get("pdf_pages", 0),
                "export_success": pdf_report.get("export_success", False),
                "errors": pdf_report.get("errors", [])
            },
            "output_files": {
                "docx": "workspace/output/final.docx",
                "pdf": "workspace/exported/final.pdf",
                "reports": "workspace/reports/",
                "logs": "workspace/logs/"
            }
        }

        output_path = self.reports_dir / "processing_summary.json"
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)

        print(f"[INFO] Summary report generated: {output_path}")
        return summary


if __name__ == "__main__":
    generator = ReportGenerator()
    generator.generate_summary_report()