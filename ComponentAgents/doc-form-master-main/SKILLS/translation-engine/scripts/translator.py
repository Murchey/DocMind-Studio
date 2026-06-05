import json

from pathlib import Path

from deep_translator import GoogleTranslator
from langdetect import detect


class TranslationEngine:

    def __init__(
        self,
        ast_path,
        target_language="en"
    ):

        self.ast_path = Path(ast_path)

        self.target_language = target_language

        self.ast = self.load_ast()

        self.report = {
            "source_language": None,
            "target_language": target_language,
            "translated_paragraphs": 0,
            "protected_nodes": 0,
            "failed_translations": 0
        }

        self.mapping = []

    def load_ast(self):

        with open(
            self.ast_path,
            "r",
            encoding="utf-8"
        ) as f:

            return json.load(f)

    def detect_language(self):

        sample_text = ""

        for paragraph in self.ast.get(
            "paragraphs",
            []
        )[:5]:

            sample_text += paragraph.get(
                "text",
                ""
            )

        detected = detect(sample_text)

        self.report[
            "source_language"
        ] = detected

        return detected

    def is_protected_text(self, text):

        protected_keywords = [
            "Figure",
            "Table",
            "http",
            "https",
            "DOI"
        ]

        for keyword in protected_keywords:

            if keyword in text:
                return True

        return False

    def translate_paragraphs(self):

        translator = GoogleTranslator(
            source="auto",
            target=self.target_language
        )

        for paragraph in self.ast.get(
            "paragraphs",
            []
        ):

            text = paragraph.get(
                "text",
                ""
            ).strip()

            if not text:
                continue

            if self.is_protected_text(text):

                self.report[
                    "protected_nodes"
                ] += 1

                continue

            try:

                translated = translator.translate(
                    text
                )

                paragraph[
                    "translated_text"
                ] = translated

                self.mapping.append({
                    "source_paragraph_id":
                    paragraph["id"],

                    "translated_paragraph_id":
                    paragraph["id"]
                })

                self.report[
                    "translated_paragraphs"
                ] += 1

            except Exception:

                self.report[
                    "failed_translations"
                ] += 1

                paragraph[
                    "translated_text"
                ] = text

    def export_translated_ast(self):

        output_dir = Path(
            "workspace/translated"
        )

        output_dir.mkdir(
            parents=True,
            exist_ok=True
        )

        with open(
            output_dir /
            "translated_ast.json",
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                self.ast,
                f,
                ensure_ascii=False,
                indent=2
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
            "translation_report.json",
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                {
                    "report": self.report,
                    "mapping": self.mapping
                },
                f,
                ensure_ascii=False,
                indent=2
            )

    def run(self):

        self.detect_language()

        self.translate_paragraphs()

        self.export_translated_ast()

        self.export_report()

        print(
            "[INFO] Translation completed"
        )


if __name__ == "__main__":

    engine = TranslationEngine(
        "workspace/parsed/document_ast.json",
        target_language="en"
    )

    engine.run()