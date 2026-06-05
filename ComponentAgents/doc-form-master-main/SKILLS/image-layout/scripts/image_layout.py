import json
import zipfile
from pathlib import Path

from PIL import Image
from lxml import etree


class ImageLayoutOptimizer:

    def __init__(self, docx_path):

        self.docx_path = Path(docx_path)

        self.report = {
            "total_images": 0,
            "scaled_images": 0,
            "cross_page_fixed": 0,
            "caption_fixed": 0,
            "relationship_errors": 0
        }

        self.images = []

    def extract_images(self):

        with zipfile.ZipFile(
            self.docx_path,
            "r"
        ) as zip_ref:

            media_files = [
                f for f in zip_ref.namelist()
                if f.startswith("word/media/")
            ]

            self.report["total_images"] = (
                len(media_files)
            )

            for idx, image_path in enumerate(
                media_files
            ):

                image_data = zip_ref.read(
                    image_path
                )

                temp_path = (
                    Path("workspace/temp")
                    / f"image_{idx}"
                )

                temp_path.parent.mkdir(
                    parents=True,
                    exist_ok=True
                )

                with open(temp_path, "wb") as f:
                    f.write(image_data)

                try:

                    with Image.open(temp_path) as img:

                        width, height = img.size

                        self.images.append({
                            "id": idx,
                            "path": image_path,
                            "width": width,
                            "height": height,
                            "keep_ratio": True,
                            "alignment": "center"
                        })

                except Exception:

                    self.report[
                        "relationship_errors"
                    ] += 1

    def optimize_image_size(self):

        MAX_WIDTH = 1200

        for image in self.images:

            if image["width"] > MAX_WIDTH:

                scale_ratio = (
                    MAX_WIDTH / image["width"]
                )

                image["width"] = MAX_WIDTH

                image["height"] = int(
                    image["height"]
                    * scale_ratio
                )

                self.report[
                    "scaled_images"
                ] += 1

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

        if not relationships:

            self.report[
                "relationship_errors"
            ] += 1

            raise ValueError(
                "Relationship validation failed"
            )

    def export_layout_report(self):

        output_dir = Path(
            "workspace/reports"
        )

        output_dir.mkdir(
            parents=True,
            exist_ok=True
        )

        with open(
            output_dir /
            "image_layout_report.json",
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                self.report,
                f,
                ensure_ascii=False,
                indent=2
            )

    def export_image_ast(self):

        output_dir = Path(
            "workspace/optimized"
        )

        output_dir.mkdir(
            parents=True,
            exist_ok=True
        )

        with open(
            output_dir /
            "image_layout_ast.json",
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                self.images,
                f,
                ensure_ascii=False,
                indent=2
            )

    def run(self):

        self.validate_relationships()

        self.extract_images()

        self.optimize_image_size()

        self.export_layout_report()

        self.export_image_ast()

        print(
            "[INFO] Image layout optimization completed"
        )


if __name__ == "__main__":

    optimizer = ImageLayoutOptimizer(
        "workspace/input/example.docx"
    )

    optimizer.run()