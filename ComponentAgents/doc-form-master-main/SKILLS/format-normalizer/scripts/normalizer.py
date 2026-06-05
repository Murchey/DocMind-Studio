import json
from pathlib import Path


class FormatNormalizer:
    def __init__(self, ast_path, config_path=None, smart_mode=False):

        self.ast_path = Path(ast_path)
        self.config_path = config_path
        self.smart_mode = smart_mode

        self.ast = self.load_ast()
        self.template_config = self.load_template_config()

        self.fix_report = {
            "paragraph_fixes": 0,
            "font_fixes": 0,
            "heading_fixes": 0,
            "table_fixes": 0,
            "heading_misclass_fixes": 0,
            "mode": "smart" if smart_mode else "standard"
        }

    def load_ast(self):

        with open(
            self.ast_path,
            "r",
            encoding="utf-8"
        ) as f:

            return json.load(f)

    def load_template_config(self):
        if self.config_path and Path(self.config_path).exists():
            with open(self.config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    @staticmethod
    def _is_protected(paragraph):
        section = paragraph.get("section", "")
        if section == "cover":
            return True
        if section == "toc":
            return True
        return False

    def _is_list_paragraph(self, paragraph):
        text = (paragraph.get("text") or "").strip()
        if not text:
            return False

        import re
        list_patterns = [
            r'^\d+[\.\、\)）]',
            r'^[①②③④⑤⑥⑦⑧⑨⑩]',
            r'^[一二三四五六七八九十]+[\.\、]',
            r'^[a-zA-Z][\.\、\)]',
            r'^[\-\•\·\▪\‣\⁃]',
            r'^\(\d+\)',
            r'^（\d+）',
            r'^\[[\d\w]\]',
        ]
        for pattern in list_patterns:
            if re.match(pattern, text):
                return True
        return False

    def normalize_paragraphs(self):

        for paragraph in self.ast.get("paragraphs", []):

            if self._is_protected(paragraph):
                continue

            style = (paragraph.get("style") or "").strip()
            if style.startswith("Heading"):
                continue

            if self.smart_mode:
                if self._is_list_paragraph(paragraph):
                    continue

                if "alignment" not in paragraph:
                    paragraph["alignment"] = "JUSTIFY"
            else:
                paragraph["alignment"] = "JUSTIFY"
                paragraph["line_spacing"] = 1.5
                paragraph["first_line_indent"] = 2

            self.fix_report["paragraph_fixes"] += 1

    def normalize_fonts(self):

        chinese_font = "宋体"
        english_font = "Times New Roman"

        fonts_config = self.template_config.get("fonts", {})
        if fonts_config:
            chinese_config = fonts_config.get("chinese", {})
            if chinese_config.get("family"):
                chinese_font = chinese_config["family"]
            english_config = fonts_config.get("english", {})
            if english_config.get("family"):
                english_font = english_config["family"]

        common_chinese_fonts = [
            "宋体", "黑体", "仿宋", "楷体", "微软雅黑",
            "SimSun", "SimHei", "FangSong", "KaiTi",
            "Noto Serif CJK", "Noto Sans CJK"
        ]
        common_english_fonts = [
            "Times New Roman", "Arial", "Calibri", "Cambria",
            "Georgia", "Verdana", "Helvetica"
        ]

        for paragraph in self.ast.get("paragraphs", []):

            if self._is_protected(paragraph):
                continue

            style = (paragraph.get("style") or "").strip()
            is_heading = style.startswith("Heading")

            for run in paragraph.get("runs", []):

                if run.get("type") == "image":
                    continue

                if run.get("type") == "formula":
                    continue

                text = run.get("text", "")

                if self.smart_mode and not is_heading:
                    current_font = run.get("font_name", "")
                    if current_font:
                        is_chinese_text = self.contains_chinese(text)
                        if is_chinese_text:
                            if any(f in current_font for f in common_chinese_fonts):
                                continue
                        else:
                            if any(f in current_font for f in common_english_fonts):
                                continue

                if self.contains_chinese(text):
                    run["font_name"] = chinese_font
                else:
                    run["font_name"] = english_font

                if not self.smart_mode:
                    run["font_size"] = "12pt"

                self.fix_report["font_fixes"] += 1

    @staticmethod
    def _estimate_text_chars(text):
        if not text:
            return 0
        count = 0
        for char in text:
            if '\u4e00' <= char <= '\u9fff':
                count += 2
            elif not char.isspace():
                count += 1
        return count

    def _is_heading_misclassified_body(self, paragraph):
        style = paragraph.get("style", "") or ""
        style_lower = style.lower()
        if 'heading 2' not in style_lower and 'heading 3' not in style_lower:
            return False
        text = paragraph.get("text", "").strip()
        char_count = self._estimate_text_chars(text)
        if char_count <= 60:
            return False
        if any(c in text for c in ['。', '，', '；', '、', '（', '）']):
            return True
        return False

    def normalize_headings(self):

        heading_config = self.template_config.get("heading", {})

        level_configs = {
            1: heading_config.get("level1", {}),
            2: heading_config.get("level2", {}),
            3: heading_config.get("level3", {})
        }

        for paragraph in self.ast.get("paragraphs", []):

            style = paragraph.get("style", "") or ""

            if self._is_heading_misclassified_body(paragraph):
                paragraph["style"] = "Normal"
                paragraph.pop("bold", None)
                for run in paragraph.get("runs", []):
                    if run.get("type") == "image":
                        continue
                    run["font_name"] = None
                self.fix_report["heading_misclass_fixes"] = self.fix_report.get("heading_misclass_fixes", 0) + 1
                style = "Normal"

            if "Heading" in style:

                paragraph["bold"] = True

                level = None
                style_lower = style.lower()
                if 'heading 1' in style_lower or 'heading1' in style_lower:
                    level = 1
                elif 'heading 2' in style_lower or 'heading2' in style_lower:
                    level = 2
                elif 'heading 3' in style_lower or 'heading3' in style_lower:
                    level = 3

                if level and level in level_configs:
                    lvl_cfg = level_configs[level]
                    lvl_alignment = lvl_cfg.get("alignment", "CENTER" if level == 1 else "LEFT")
                    paragraph["alignment"] = lvl_alignment
                    lvl_size = lvl_cfg.get("size", 16 if level == 1 else 14 if level == 2 else 13)
                    for run in paragraph.get("runs", []):
                        if run.get("type") == "image":
                            continue
                        if run.get("type") == "formula":
                            continue
                        run["font_size"] = f"{lvl_size}pt"
                        if lvl_cfg.get("font"):
                            run["font_name"] = lvl_cfg["font"]
                else:
                    paragraph["alignment"] = "CENTER" if level == 1 else "LEFT"

                self.fix_report["heading_fixes"] += 1

    def normalize_tables(self):

        for table in self.ast.get("tables", []):

            table["alignment"] = "CENTER"

            table["auto_fit"] = True

            self.fix_report["table_fixes"] += 1

    @staticmethod
    def contains_chinese(text):

        for char in text:
            if '\u4e00' <= char <= '\u9fff':
                return True

        return False

    def export_normalized_ast(self):

        output_dir = Path(
            "workspace/normalized"
        )

        output_dir.mkdir(
            parents=True,
            exist_ok=True
        )

        with open(
            output_dir / "normalized_ast.json",
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                self.ast,
                f,
                ensure_ascii=False,
                indent=2
            )

    def export_fix_report(self):

        report_dir = Path("workspace/reports")

        report_dir.mkdir(
            parents=True,
            exist_ok=True
        )

        with open(
            report_dir / "fix_report.json",
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                self.fix_report,
                f,
                ensure_ascii=False,
                indent=2
            )

    def run(self):

        self.normalize_paragraphs()

        self.normalize_fonts()

        self.normalize_headings()

        self.normalize_tables()

        self.export_normalized_ast()

        self.export_fix_report()

        print(
            f"[INFO] Format normalization completed (mode: {'smart' if self.smart_mode else 'standard'})"
        )


if __name__ == "__main__":

    normalizer = FormatNormalizer(
        "workspace/parsed/document_ast.json"
    )

    normalizer.run()
