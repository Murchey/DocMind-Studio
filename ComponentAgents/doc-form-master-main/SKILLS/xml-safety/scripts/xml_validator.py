import json
import zipfile

from pathlib import Path

from lxml import etree


class XMLSafetyValidator:

    def __init__(self, docx_path):

        self.docx_path = Path(docx_path)

        self.required_files = [
            "[Content_Types].xml",
            "_rels/.rels",
            "word/document.xml",
            "word/styles.xml",
            "word/numbering.xml"
        ]

        self.report = {
            "xml_files": 0,
            "namespace_count": 0,
            "relationship_count": 0,
            "orphan_relationships": 0,
            "xml_errors": 0
        }

    def validate_zip_structure(self):

        with zipfile.ZipFile(
            self.docx_path,
            "r"
        ) as zip_ref:

            file_list = zip_ref.namelist()

            for required_file in (
                self.required_files
            ):

                if required_file not in file_list:

                    raise FileNotFoundError(
                        f"Missing: "
                        f"{required_file}"
                    )

    def validate_xml_files(self):

        with zipfile.ZipFile(
            self.docx_path,
            "r"
        ) as zip_ref:

            xml_files = [
                f for f in zip_ref.namelist()
                if f.endswith(".xml")
            ]

            self.report[
                "xml_files"
            ] = len(xml_files)

            for xml_file in xml_files:

                try:

                    xml_content = (
                        zip_ref.read(xml_file)
                    )

                    etree.fromstring(
                        xml_content
                    )

                except Exception:

                    self.report[
                        "xml_errors"
                    ] += 1

    def validate_namespaces(self):

        with zipfile.ZipFile(
            self.docx_path,
            "r"
        ) as zip_ref:

            xml_content = zip_ref.read(
                "word/document.xml"
            )

        root = etree.fromstring(xml_content)

        namespaces = root.nsmap

        required_namespaces = [
            "w",
            "r",
            "m"
        ]

        for namespace in (
            required_namespaces
        ):

            if namespace not in namespaces:

                raise ValueError(
                    f"Missing namespace: "
                    f"{namespace}"
                )

        self.report[
            "namespace_count"
        ] = len(namespaces)

    def validate_relationships(self):

        with zipfile.ZipFile(
            self.docx_path,
            "r"
        ) as zip_ref:

            rels_xml = zip_ref.read(
                "word/_rels/document.xml.rels"
            )

        root = etree.fromstring(rels_xml)

        relationships = root.findall(
            ".//{*}Relationship"
        )

        self.report[
            "relationship_count"
        ] = len(relationships)

        relationship_ids = set()

        for rel in relationships:

            rel_id = rel.attrib.get("Id")

            if rel_id in relationship_ids:

                self.report[
                    "orphan_relationships"
                ] += 1

            relationship_ids.add(rel_id)

    def export_report(self):

        output_dir = Path(
            "workspace/reports"
        )

        output_dir.mkdir(
            parents=True,
            exist_ok=True
        )

        with open(
            output_dir /
            "xml_safety_report.json",
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

        self.validate_zip_structure()

        self.validate_xml_files()

        self.validate_namespaces()

        self.validate_relationships()

        self.export_report()

        print(
            "[INFO] XML validation completed"
        )


if __name__ == "__main__":

    validator = XMLSafetyValidator(
        "workspace/input/《智能体平台应用》课程作业.docx"
    )

    validator.run()