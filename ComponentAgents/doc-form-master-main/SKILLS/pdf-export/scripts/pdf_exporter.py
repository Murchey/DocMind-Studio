import json
import platform
import subprocess
from pathlib import Path

from PyPDF2 import PdfReader


class PDFExporter:

    def __init__(self, docx_path):

        self.docx_path = Path(docx_path)

        self.output_dir = Path(
            "workspace/exported"
        )

        self.output_dir.mkdir(
            parents=True,
            exist_ok=True
        )

        self.report = {
            "export_engine": None,
            "pdf_pages": 0,
            "export_success": False,
            "errors": []
        }

    def detect_export_engine(self):

        system = platform.system()

        if system == "Windows":
            try:
                import win32com.client
                self.report["export_engine"] = "Word COM"
                return "word"
            except ImportError:
                self.report["export_engine"] = "LibreOffice"
                return "libreoffice"
        else:
            self.report["export_engine"] = "LibreOffice"
            return "libreoffice"

    def export_with_libreoffice(self):

        subprocess.run([
            "libreoffice",
            "--headless",
            "--convert-to",
            "pdf:writer_pdf_Export",
            str(self.docx_path),
            "--outdir",
            str(self.output_dir)
        ], check=True)

    def export_with_word(self):

        import win32com.client

        word = win32com.client.Dispatch("Word.Application")
        word.Visible = False
        word.DisplayAlerts = False

        pdf_path = str(self.output_dir / "final.pdf")

        try:
            doc = word.Documents.Open(str(self.docx_path))

            doc.ExportAsFixedFormat(
                OutputFileName=pdf_path,
                ExportFormat=17,
                OpenAfterExport=False,
                OptimizeFor=0,
                Range=0,
                From=1,
                To=1,
                Item=0,
                IncludeDocProps=True,
                KeepIRM=True,
                CreateBookmarks=0,
                DocStructureTags=True,
                BitmapMissingFonts=False,
                UseISO19005_1=False
            )

            doc.Close()
        finally:
            word.Quit()

    def validate_pdf(self):

        pdf_path = (
            self.output_dir / "final.pdf"
        )

        if not pdf_path.exists():

            raise FileNotFoundError(
                "PDF export failed"
            )

        reader = PdfReader(
            str(pdf_path)
        )

        self.report["pdf_pages"] = (
            len(reader.pages)
        )

    def export_report(self):

        report_dir = Path(
            "workspace/reports"
        )

        report_dir.mkdir(
            parents=True,
            exist_ok=True
        )

        with open(
            report_dir /
            "pdf_export_report.json",
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                self.report,
                f,
                ensure_ascii=False,
                indent=2
            )

    def run(self):

        try:

            engine = (
                self.detect_export_engine()
            )

            if engine == "word":
                self.export_with_word()

            else:
                self.export_with_libreoffice()

            self.validate_pdf()

            self.report[
                "export_success"
            ] = True

            self.export_report()

            print(
                "[INFO] PDF export completed"
            )

        except Exception as e:

            self.report["errors"].append(
                str(e)
            )

            self.export_report()

            print(
                f"[ERROR] {e}"
            )


if __name__ == "__main__":

    exporter = PDFExporter(
        "workspace/output/final.docx"
    )

    exporter.run()