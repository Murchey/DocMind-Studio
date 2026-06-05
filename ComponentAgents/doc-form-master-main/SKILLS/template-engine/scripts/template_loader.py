import json
import yaml

from pathlib import Path


class TemplateLoader:

    def __init__(self):

        self.template_dirs = [
            Path(
                "skills/template-engine/templates"
            ),
            Path(
                "skills/format-normalizer/custom"
            )
        ]

        self.templates = []

    def scan_templates(self):

        for template_dir in self.template_dirs:

            if not template_dir.exists():
                continue

            for file in template_dir.iterdir():

                if file.suffix.lower() in [
                    ".yaml",
                    ".yml",
                    ".json"
                ]:

                    self.templates.append(file)

    def show_templates(self):

        print("\n可用模板：\n")

        for idx, template in enumerate(
            self.templates,
            start=1
        ):

            print(
                f"{idx}. {template.name}"
            )

    def select_template(self):

        self.show_templates()

        selected = input(
            "\n请选择模板编号："
        )

        selected = int(selected) - 1

        return self.templates[selected]

    def load_template(self, template_path):

        if template_path.suffix.lower() in [
            ".yaml",
            ".yml"
        ]:

            with open(
                template_path,
                "r",
                encoding="utf-8"
            ) as f:

                return yaml.safe_load(f)

        elif template_path.suffix.lower() == ".json":

            with open(
                template_path,
                "r",
                encoding="utf-8"
            ) as f:

                return json.load(f)

        else:

            raise ValueError(
                "Unsupported template type"
            )

    def validate_template(self, config):

        required_fields = [
            "fonts",
            "paragraph",
            "heading"
        ]

        missing_fields = []

        for field in required_fields:

            if field not in config:
                missing_fields.append(field)

        if missing_fields:

            raise ValueError(
                f"Missing fields: "
                f"{missing_fields}"
            )

    def export_config(self, config):

        output_dir = Path(
            "workspace/validated"
        )

        output_dir.mkdir(
            parents=True,
            exist_ok=True
        )

        with open(
            output_dir /
            "template_config.json",
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                config,
                f,
                ensure_ascii=False,
                indent=2
            )

    def run(self, template_name=None):

        self.scan_templates()

        if template_name:
            template_path = None
            for template in self.templates:
                if template.name == template_name:
                    template_path = template
                    break
            if not template_path:
                raise ValueError(
                    f"Template not found: {template_name}"
                )
        else:
            template_path = (
                self.select_template()
            )

        config = self.load_template(
            template_path
        )

        self.validate_template(config)

        self.export_config(config)

        print(
            f"[INFO] "
            f"Loaded template: "
            f"{template_path.name}"
        )


if __name__ == "__main__":

    loader = TemplateLoader()

    loader.run("chinese_academic.yaml")    