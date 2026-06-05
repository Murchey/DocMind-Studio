import json
import zipfile
from pathlib import Path

from lxml import etree


class FormulaDetector:

    def __init__(self, docx_path):

        self.docx_path = Path(docx_path)

        self.namespaces = {
            "m": (
                "http://schemas.openxmlformats.org/"
                "officeDocument/2006/math"
            )
        }

        self.report = {
            "total_formulas": 0,
            "omml_formulas": 0,
            "inline_formulas": 0,
            "block_formulas": 0,
            "namespace_errors": 0
        }

        self.formulas = []

    def load_document_xml(self):

        with zipfile.ZipFile(
            self.docx_path,
            "r"
        ) as zip_ref:

            return zip_ref.read(
                "word/document.xml"
            )

    def parse_formulas(self):

        xml_content = self.load_document_xml()

        root = etree.fromstring(xml_content)

        formulas = root.xpath(
            "//m:oMath",
            namespaces=self.namespaces
        )

        self.report["total_formulas"] = len(formulas)

        for idx, formula in enumerate(formulas):

            formula_xml = etree.tostring(
                formula,
                encoding="utf-8"
            ).decode("utf-8")

            self.formulas.append({
                "id": idx,
                "type": "OMML",
                "xml": formula_xml
            })

            self.report["omml_formulas"] += 1

    def validate_namespace(self):

        required_namespace = (
            "http://schemas.openxmlformats.org/"
            "officeDocument/2006/math"
        )

        if (
            self.namespaces["m"]
            != required_namespace
        ):

            self.report[
                "namespace_errors"
            ] += 1

            raise ValueError(
                "Math namespace validation failed"
            )

    def export_report(self):

        output_dir = Path(
            "workspace/reports"
        )

        output_dir.mkdir(
            parents=True,
            exist_ok=True
        )

        with open(
            output_dir / "formula_report.json",
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                self.report,
                f,
                ensure_ascii=False,
                indent=2
            )

    def export_formulas(self):

        output_dir = Path(
            "workspace/protected"
        )

        output_dir.mkdir(
            parents=True,
            exist_ok=True
        )

        with open(
            output_dir / "protected_formulas.json",
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                self.formulas,
                f,
                ensure_ascii=False,
                indent=2
            )

    def run(self):

        self.validate_namespace()

        self.parse_formulas()

        self.export_report()

        self.export_formulas()

        print(
            "[INFO] Formula protection completed"
        )


if __name__ == "__main__":

    detector = FormulaDetector(
        "workspace/input/《智能体平台应用》课程作业.docx"
    )

    detector.run()