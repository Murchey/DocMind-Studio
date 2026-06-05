import json
import yaml
from pathlib import Path


class TemplateLoader:

    def __init__(self):

        self.template_dir = Path(
            "skills/format-normalizer/custom"
        )

    def scan_templates(self):

        templates = []

        for file in self.template_dir.iterdir():

            if file.suffix.lower() in [
                ".yaml",
                ".yml",
                ".json"
            ]:
                templates.append(file.name)

        return templates

    def ask_user_template(self):

        templates = self.scan_templates()

        print("\n可用模板：\n")

        for idx, template in enumerate(templates, start=1):
            print(f"{idx}. {template}")

        selected = input(
            "\n请选择需要使用的模板编号："
        )

        selected = int(selected) - 1

        return templates[selected]

    def load_template(self, template_name):

        template_path = (
            self.template_dir / template_name
        )

        if not template_path.exists():
            raise FileNotFoundError(
                f"模板不存在: {template_name}"
            )

        if template_path.suffix in [
            ".yaml",
            ".yml"
        ]:

            with open(
                template_path,
                "r",
                encoding="utf-8"
            ) as f:

                return yaml.safe_load(f)

        elif template_path.suffix == ".json":

            with open(
                template_path,
                "r",
                encoding="utf-8"
            ) as f:

                return json.load(f)

        else:
            raise ValueError(
                "不支持的模板格式"
            )


if __name__ == "__main__":

    loader = TemplateLoader()

    selected_template = (
        loader.ask_user_template()
    )

    template_config = loader.load_template(
        selected_template
    )

    print("\n已加载模板：")
    print(template_config)