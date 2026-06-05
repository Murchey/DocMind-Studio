import json

from pathlib import Path

from matplotlib import font_manager


class FontManager:

    def __init__(self):

        self.available_fonts = []

        self.missing_fonts = []

        self.fallback_mapping = {}

        self.required_fonts = [
            "宋体",
            "黑体",
            "Times New Roman",
            "Consolas"
        ]

        self.fallback_rules = {
            "宋体": [
                "SimSun",
                "Noto Serif CJK SC"
            ],

            "黑体": [
                "SimHei",
                "Noto Sans CJK SC"
            ],

            "Times New Roman": [
                "Liberation Serif"
            ],

            "Consolas": [
                "Courier New",
                "JetBrains Mono"
            ]
        }

    def scan_system_fonts(self):

        fonts = font_manager.fontManager.ttflist

        self.available_fonts = list(
            set(font.name for font in fonts)
        )

    FONT_ALIASES = {
        "宋体": ["SimSun", "simsun", "NSimSun"],
        "黑体": ["SimHei", "simhei", "Microsoft YaHei"],
        "仿宋_GB2312": ["FangSong_GB2312", "仿宋"],
        "楷体": ["KaiTi", "kaiti"],
        "微软雅黑": ["Microsoft YaHei", "msyh"],
    }

    def _font_is_available(self, font_name):
        if font_name in self.available_fonts:
            return True
        aliases = self.FONT_ALIASES.get(font_name, [])
        for alias in aliases:
            if alias in self.available_fonts:
                return True
            for avail in self.available_fonts:
                if alias.lower() == avail.lower():
                    return True
        return False

    def validate_fonts(self):

        for font in self.required_fonts:

            if not self._font_is_available(font):

                self.missing_fonts.append(font)

                self.apply_fallback(font)

    def apply_fallback(self, missing_font):

        fallback_candidates = (
            self.fallback_rules.get(
                missing_font,
                []
            )
        )

        for candidate in fallback_candidates:

            if candidate in self.available_fonts:

                self.fallback_mapping[
                    missing_font
                ] = candidate

                return

        self.fallback_mapping[
            missing_font
        ] = "DEFAULT"

    def export_report(self):

        output_dir = Path(
            "workspace/reports"
        )

        output_dir.mkdir(
            parents=True,
            exist_ok=True
        )

        report = {
            "available_fonts_count":
            len(self.available_fonts),

            "missing_fonts":
            self.missing_fonts,

            "fallback_mapping":
            self.fallback_mapping
        }

        with open(
            output_dir /
            "font_report.json",
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                report,
                f,
                ensure_ascii=False,
                indent=2
            )

    def export_mapping(self):

        output_dir = Path(
            "workspace/validated"
        )

        output_dir.mkdir(
            parents=True,
            exist_ok=True
        )

        with open(
            output_dir /
            "font_mapping.json",
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                self.fallback_mapping,
                f,
                ensure_ascii=False,
                indent=2
            )

    def run(self):

        self.scan_system_fonts()

        self.validate_fonts()

        self.export_report()

        self.export_mapping()

        print(
            "[INFO] Font validation completed"
        )

        if self.missing_fonts:

            print(
                "\n[WARNING] Missing fonts:"
            )

            for font in self.missing_fonts:

                print(f"- {font}")


if __name__ == "__main__":

    manager = FontManager()

    manager.run()