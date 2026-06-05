import json
import zipfile
from pathlib import Path

from docx import Document
from lxml import etree


class DocxParser:
    def __init__(self, docx_path):
        self.docx_path = Path(docx_path)
        self.document = Document(docx_path)

        self.ast = {
            "metadata": {},
            "paragraphs": [],
            "tables": [],
            "images": [],
            "formulas": [],
            "styles": [],
            "sections": []
        }

    def validate_docx(self):
        if not self.docx_path.exists():
            raise FileNotFoundError(
                f"File not found: {self.docx_path}"
            )

        if self.docx_path.suffix.lower() != ".docx":
            raise ValueError(
                "Only .docx files are supported"
            )

    def parse_metadata(self):
        core = self.document.core_properties

        self.ast["metadata"] = {
            "author": core.author,
            "title": core.title,
            "created": str(core.created),
            "modified": str(core.modified)
        }

    def parse_styles(self):
        for style in self.document.styles:
            self.ast["styles"].append({
                "name": style.name,
                "type": str(style.type)
            })

    def parse_paragraphs(self):
        image_rels = self._build_image_relationship_map()

        W_NS = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
        A_NS = 'http://schemas.openxmlformats.org/drawingml/2006/main'
        R_NS = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
        M_NS = 'http://schemas.openxmlformats.org/officeDocument/2006/math'

        with zipfile.ZipFile(self.docx_path, "r") as zip_ref:
            media_cache = {}

            for idx, para in enumerate(self.document.paragraphs):
                paragraph_data = {
                    "id": idx,
                    "type": "paragraph",
                    "text": para.text,
                    "style": para.style.name if para.style else None,
                    "alignment": str(para.alignment),
                    "runs": []
                }

                for child in para._element:
                    tag_local = child.tag.split('}')[1] if '}' in child.tag else child.tag
                    ns_uri = child.tag.split('}')[0].strip('{') if '}' in child.tag else ''

                    if ns_uri == M_NS and tag_local in ('oMath', 'oMathPara'):
                        xml_str = etree.tostring(child).decode('utf-8')
                        math_texts = []
                        for mt in child.iter(f'{{{M_NS}}}t'):
                            if mt.text:
                                math_texts.append(mt.text)
                        paragraph_data["runs"].append({
                            "type": "formula",
                            "formula_type": tag_local,
                            "xml": xml_str,
                            "text": ''.join(math_texts)
                        })
                        continue

                    if child.tag != f'{{{W_NS}}}r':
                        continue

                    run_text = ''
                    run_bold = None
                    run_italic = None
                    run_underline = None
                    run_font_name = None
                    run_font_size = None

                    has_drawing = False

                    for sub_child in child:
                        tag_local = sub_child.tag.split('}')[1] if '}' in sub_child.tag else sub_child.tag

                        if tag_local == 't' and sub_child.text:
                            run_text += sub_child.text
                        elif tag_local == 'rPr':
                            for rpr_child in sub_child:
                                rpr_tag = rpr_child.tag.split('}')[1] if '}' in rpr_child.tag else rpr_child.tag
                                if rpr_tag == 'b':
                                    run_bold = True
                                elif rpr_tag == 'i':
                                    run_italic = True
                                elif rpr_tag == 'u':
                                    run_underline = True
                                elif rpr_tag == 'rFonts':
                                    run_font_name = rpr_child.get(f'{{{W_NS}}}eastAsia') or rpr_child.get(f'{{{W_NS}}}ascii')
                                elif rpr_tag == 'sz':
                                    sz_val = rpr_child.get(f'{{{W_NS}}}val')
                                    if sz_val:
                                        run_font_size = str(int(sz_val) // 2) + 'pt'
                        elif tag_local in ('drawing', 'object'):
                            has_drawing = True
                        elif tag_local == 'AlternateContent':
                            for ac_child in sub_child:
                                for drawing_elem in ac_child.iter():
                                    d_tag = drawing_elem.tag.split('}')[1] if '}' in drawing_elem.tag else drawing_elem.tag
                                    if d_tag == 'drawing':
                                        has_drawing = True

                    if has_drawing:
                        blip = child.findall(f'.//{{{A_NS}}}blip')
                        if blip:
                            rel_id = blip[0].get(f'{{{R_NS}}}embed')
                            if rel_id and rel_id in image_rels:
                                img_path = image_rels[rel_id]

                                if img_path not in media_cache:
                                    media_cache[img_path] = zip_ref.read(img_path)

                                img_data = media_cache[img_path]

                                ext = Path(img_path).suffix.lower().replace('.', '')
                                if ext in ('jpg', 'jpeg'):
                                    ext = 'jpeg'

                                import base64
                                img_b64 = base64.b64encode(img_data).decode('utf-8')

                                paragraph_data["runs"].append({
                                    "type": "image",
                                    "image_data": img_b64,
                                    "image_format": ext
                                })

                    if run_data := self._build_text_run(run_text, run_bold, run_italic, run_underline, run_font_name, run_font_size):
                        paragraph_data["runs"].append(run_data)

                self.ast["paragraphs"].append(paragraph_data)

    @staticmethod
    def _build_text_run(text, bold, italic, underline, font_name, font_size):
        if not text:
            return None
        run_data = {
            "text": text,
            "bold": bold,
            "italic": italic,
            "underline": underline,
            "font_name": font_name,
            "font_size": font_size
        }
        return run_data

    def _build_image_relationship_map(self):
        image_rels = {}
        try:
            with zipfile.ZipFile(self.docx_path, "r") as zip_ref:
                if "word/_rels/document.xml.rels" in zip_ref.namelist():
                    rels_xml = zip_ref.read("word/_rels/document.xml.rels")
                    rels_root = etree.fromstring(rels_xml)
                    for rel in rels_root:
                        rel_id = rel.get('Id')
                        target = rel.get('Target', '')
                        if target.startswith('media/'):
                            image_rels[rel_id] = f'word/{target}'
        except:
            pass
        return image_rels

    def parse_tables(self):
        for table_idx, table in enumerate(self.document.tables):

            table_data = {
                "id": table_idx,
                "rows": []
            }

            for row in table.rows:
                row_data = []

                for cell in row.cells:
                    row_data.append(cell.text)

                table_data["rows"].append(row_data)

            self.ast["tables"].append(table_data)

    def extract_images(self):
        with zipfile.ZipFile(self.docx_path, "r") as zip_ref:

            media_files = [
                f for f in zip_ref.namelist()
                if f.startswith("word/media/")
            ]

            for idx, image_path in enumerate(media_files):

                self.ast["images"].append({
                    "id": idx,
                    "path": image_path
                })

    def parse_formulas(self):

        with zipfile.ZipFile(self.docx_path, "r") as zip_ref:
            xml_content = zip_ref.read("word/document.xml")

        root = etree.fromstring(xml_content)

        namespaces = {
            "m": (
                "http://schemas.openxmlformats.org/"
                "officeDocument/2006/math"
            )
        }

        formulas = root.xpath(
            "//m:oMath",
            namespaces=namespaces
        )

        for idx, formula in enumerate(formulas):

            self.ast["formulas"].append({
                "id": idx,
                "xml": etree.tostring(
                    formula
                ).decode("utf-8")
            })

    def export_ast(self, output_path):

        output_path = Path(output_path)

        output_path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        with open(
            output_path,
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                self.ast,
                f,
                ensure_ascii=False,
                indent=2
            )

    def run(self):

        self.validate_docx()

        self.parse_metadata()

        self.parse_styles()

        self.parse_paragraphs()

        self.parse_tables()

        self.extract_images()

        self.parse_formulas()

        self._identify_sections()

        self.export_ast(
            "workspace/parsed/document_ast.json"
        )

        print(
            "[INFO] AST exported successfully"
        )

    def _identify_sections(self):
        import re

        paras = self.ast.get("paragraphs", [])
        if not paras:
            return

        CHINESE_NUMS = "一二三四五六七八九十百"
        H1_PATTERN = re.compile(r'^第[{}0-9一二三四五六七八九十]+[章节部篇]'.format(CHINESE_NUMS))
        H1_PATTERN_NUM = re.compile(r'^\d+\s+\S')
        H2_PATTERN_CN = re.compile(r'^[一二三四五六七八九十]+[、．.]')
        H2_PATTERN_KW = re.compile(r'^(引言|摘要|结论|参考文献|致谢|附录|abstract|references|introduction|conclusion|summary)', re.IGNORECASE)
        H3_PATTERN = re.compile(r'^\d+\.\d+[\.\s]')

        def detect_heading_level(p):
            style = (p.get("style") or "").lower()
            text = (p.get("text") or "").strip()
            if not text:
                return None, None
            if "heading 1" in style:
                return "Heading 1", text
            if "heading 2" in style:
                return "Heading 2", text
            if "heading 3" in style:
                return "Heading 3", text

            if len(text) > 100:
                return None, None

            if H1_PATTERN.match(text):
                return "Heading 1", text
            if H1_PATTERN_NUM.match(text) and len(text) < 50:
                return "Heading 1", text
            if H2_PATTERN_CN.match(text):
                return "Heading 2", text
            if H2_PATTERN_KW.match(text.lower()):
                return "Heading 2", text
            if H3_PATTERN.match(text):
                return "Heading 3", text

            return None, None

        cover_end = 0
        toc_start = -1
        toc_end = -1

        toc_keywords = ["目录", "目 录", "目  录", "table of contents", "contents"]

        for i, p in enumerate(paras):
            text = (p.get("text") or "").strip()
            text_lower = text.lower()
            level, _ = detect_heading_level(p)

            if level == "Heading 1":
                if toc_start >= 0 and toc_end < 0:
                    toc_end = i
                if cover_end == 0:
                    cover_end = i
                break

            if level:
                if cover_end == 0:
                    cover_end = i
                    break

            if any(kw in text_lower for kw in toc_keywords):
                toc_start = i

            if "toc" in (p.get("style") or "").lower() or "目录" in (p.get("style") or "").lower():
                if toc_start < 0:
                    toc_start = i
                toc_end = i + 1

        if cover_end == 0:
            for i, p in enumerate(paras):
                text = (p.get("text") or "").strip()
                if text and len(text) > 5:
                    level, _ = detect_heading_level(p)
                    if level:
                        cover_end = i
                        break

        if toc_start >= 0 and toc_end < 0:
            for i in range(toc_start + 1, len(paras)):
                level, _ = detect_heading_level(paras[i])
                text = (paras[i].get("text") or "").strip()
                if level == "Heading 1" or (text and not level and len(text) > 20):
                    toc_end = i
                    break
            if toc_end < 0:
                toc_end = min(toc_start + 20, len(paras))

        for i, p in enumerate(paras):
            if toc_start >= 0 and toc_start <= i < toc_end:
                p["section"] = "toc"
            elif i < cover_end:
                p["section"] = "cover"
            else:
                p["section"] = "body"

        self.ast["section_regions"] = {
            "cover_end": cover_end,
            "toc_start": toc_start,
            "toc_end": toc_end
        }


if __name__ == "__main__":
    import sys

    input_path = sys.argv[1] if len(sys.argv) > 1 else "workspace/input/input.docx"
    parser = DocxParser(input_path)
    parser.run()