"""DOCX XML auto-fixer - fixes formatting issues at XML level."""
import copy
import shutil
import zipfile
from pathlib import Path
from lxml import etree

WML = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"


class DocxFixer:
    """Fix DOCX formatting by directly modifying XML internals."""

    def __init__(self, docx_path, rules_path=None):
        self.docx_path = Path(docx_path)
        self._ns = {"w": WML}
        self.rules = self._load_rules(rules_path)
        self.fixes_applied = []

    def _qn(self, tag):
        prefix, local = tag.split(":")
        return "{%s}%s" % (self._ns[prefix], local)

    def _load_rules(self, rules_path):
        if rules_path is None:
            rules_path = Path(__file__).parent.parent / "rules" / "chinese_academic_rules.yaml"
        try:
            import yaml
            with open(rules_path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f)
        except Exception:
            return self._default_rules()

    def _default_rules(self):
        return {
            "fonts": {
                "body": {"chinese_family": "宋体", "english_family": "Times New Roman", "size_pt": 12},
                "heading1": {"family": "黑体", "size_pt": 14, "bold": True},
                "heading2": {"family": "黑体", "size_pt": 12, "bold": True},
                "heading3": {"family": "黑体", "size_pt": 12, "bold": True},
            },
            "paragraph": {
                "alignment": "both",
                "line_spacing": {"value": 1.5},
                "first_line_indent": {"value_chars": 2},
            },
            "heading": {
                "level1": {"alignment": "center"},
                "level2": {"alignment": "left"},
                "level3": {"alignment": "left"},
            },
            "page": {
                "margins": {"top_cm": 2.54, "bottom_cm": 2.54, "left_cm": 3.17, "right_cm": 2.54},
            },
        }

    def fix(self, output_path=None):
        """Apply all fixes and save to output_path (or overwrite in place)."""
        if output_path is None:
            output_path = self.docx_path
        else:
            output_path = Path(output_path)

        # Always use temp file to avoid read/write conflict on same file
        tmp_src = self.docx_path.with_suffix(".docx.src")
        tmp_out = self.docx_path.with_suffix(".docx.fixed")
        shutil.copy2(self.docx_path, tmp_src)

        with zipfile.ZipFile(tmp_src, "r") as zin:
            with zipfile.ZipFile(tmp_out, "w", zipfile.ZIP_DEFLATED) as zout:
                for item in zin.infolist():
                    data = zin.read(item.filename)
                    if item.filename == "word/document.xml":
                        data = self._fix_document_xml(data)
                    zout.writestr(item, data)

        tmp_src.unlink(missing_ok=True)

        # Replace target with fixed version
        if output_path.exists():
            output_path.unlink()
        shutil.move(str(tmp_out), str(output_path))

        print(f"[INFO] Fixed DOCX saved to {output_path}")
        return self.fixes_applied

    # ==================== document.xml fixes ====================

    def _fix_document_xml(self, data):
        root = etree.fromstring(data)
        body = root.find(self._qn("w:body"))
        if body is None:
            return data

        # Fix margins in sectPr
        sect_pr = body.find(self._qn("w:sectPr"))
        if sect_pr is not None:
            self._fix_margins(sect_pr)

        # Read styles to resolve style hierarchy
        styles = self._read_styles_from_data()

        # Fix each paragraph
        for p_elem in body.findall(self._qn("w:p")):
            self._fix_paragraph(p_elem, styles)

        # Fix each table
        for tbl in body.findall(self._qn("w:tbl")):
            self._fix_table(tbl)

        return etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)

    def _fix_margins(self, sect_pr):
        pg_mar = sect_pr.find(self._qn("w:pgMar"))
        if pg_mar is None:
            return

        margin_rules = self.rules.get("page", {}).get("margins", {})
        target = {
            "top": margin_rules.get("top_cm", 2.54),
            "bottom": margin_rules.get("bottom_cm", 2.54),
            "left": margin_rules.get("left_cm", 3.17),
            "right": margin_rules.get("right_cm", 2.54),
        }

        for key, target_cm in target.items():
            attr = self._qn(f"w:{key}")
            current_twips = pg_mar.get(attr)
            if current_twips is None:
                continue
            try:
                current_cm = int(current_twips) * 2.54 / 1440.0
                if abs(current_cm - target_cm) > 0.1:
                    new_twips = int(target_cm * 1440 / 2.54)
                    pg_mar.set(attr, str(new_twips))
                    self.fixes_applied.append({
                        "type": "margin",
                        "detail": f"{key}边距: {current_cm:.2f}cm → {target_cm}cm"
                    })
            except (ValueError, TypeError):
                pass

    def _fix_paragraph(self, p_elem, styles):
        ppr = p_elem.find(self._qn("w:pPr"))
        if ppr is None:
            ppr = etree.SubElement(p_elem, self._qn("w:pPr"))
            # Move pPr to be the first child
            p_elem.remove(ppr)
            p_elem.insert(0, ppr)

        # Resolve style
        style_id = ""
        pstyle = ppr.find(self._qn("w:pStyle"))
        if pstyle is not None:
            style_id = pstyle.get(self._qn("w:val"), "")

        is_heading = style_id.lower().startswith("heading")
        heading_level = 0
        if is_heading:
            try:
                heading_level = int(style_id[-1])
            except (ValueError, IndexError):
                pass

        # Get text for context
        text = "".join(t.text or "" for t in p_elem.findall(f".//{self._qn('w:t')}"))

        # Skip empty paragraphs and cover/toc
        if not text.strip() and not p_elem.findall(f".//{self._qn('w:drawing')}"):
            return

        # Determine target formatting
        if is_heading:
            rule_key = f"heading{heading_level}"
            font_rules = self.rules.get("fonts", {}).get(rule_key)
            # Heading4+ falls back to heading3, then heading2, then heading1
            if font_rules is None:
                for fallback_level in range(min(heading_level, 3), 0, -1):
                    font_rules = self.rules.get("fonts", {}).get(f"heading{fallback_level}")
                    if font_rules:
                        break
                if font_rules is None:
                    font_rules = self.rules.get("fonts", {}).get("heading1", {})
            align_rules = self.rules.get("heading", {}).get(f"level{heading_level}")
            if not align_rules:
                for fallback_level in range(min(heading_level, 3), 0, -1):
                    align_rules = self.rules.get("heading", {}).get(f"level{fallback_level}")
                    if align_rules:
                        break
                if not align_rules:
                    align_rules = {}
        else:
            font_rules = self.rules.get("fonts", {}).get("body", {})
            align_rules = self.rules.get("paragraph", {})

        # Fix alignment
        self._fix_alignment(ppr, align_rules, is_heading, text[:30])

        # Fix first line indent (body only)
        if not is_heading:
            self._fix_indentation(ppr, text[:30])

        # Fix run properties (font, size, bold)
        for r_elem in p_elem.findall(self._qn("w:r")):
            self._fix_run(r_elem, font_rules, is_heading, heading_level, text[:30])

    def _fix_alignment(self, ppr, rules, is_heading, text_ctx):
        expected = rules.get("alignment", "both")
        if is_heading:
            expected = rules.get("alignment", "left")

        jc = ppr.find(self._qn("w:jc"))
        current = jc.get(self._qn("w:val"), "") if jc is not None else ""

        # "distribute" in OOXML is equivalent to "both" (两端对齐)
        equivalent = {"both": "both", "distribute": "both",
                      "left": "left", "center": "center", "right": "right"}
        current_norm = equivalent.get(current, current)
        expected_norm = equivalent.get(expected, expected)

        if current_norm != expected_norm:
            if jc is None:
                jc = etree.SubElement(ppr, self._qn("w:jc"))
            jc.set(self._qn("w:val"), expected)
            self.fixes_applied.append({
                "type": "alignment",
                "detail": f"对齐: {current or 'none'} → {expected} ({text_ctx})"
            })

    def _fix_indentation(self, ppr, text_ctx):
        indent_rules = self.rules.get("paragraph", {}).get("first_line_indent", {})
        expected_chars = indent_rules.get("value_chars", 2)
        # 2 chars at 12pt = 2 * 240 twips = 480 twips
        target_twips = expected_chars * 240

        ind = ppr.find(self._qn("w:ind"))
        current_first_line = 0
        current_chars = None

        if ind is not None:
            fl = ind.get(self._qn("w:firstLine"))
            flc = ind.get(self._qn("w:firstLineChars"))
            try:
                current_first_line = int(fl) if fl else 0
            except (ValueError, TypeError):
                pass
            current_chars = flc

        has_indent = False
        if current_chars:
            try:
                has_indent = int(current_chars) >= expected_chars * 100
            except (ValueError, TypeError):
                pass
        # current_first_line is in points (twips / 20); target_twips is in twips
        target_points = target_twips / 20.0
        if not has_indent:
            has_indent = current_first_line >= target_points - 2

        if not has_indent:
            if ind is None:
                ind = etree.SubElement(ppr, self._qn("w:ind"))
            ind.set(self._qn("w:firstLineChars"), str(expected_chars * 100))
            ind.set(self._qn("w:firstLine"), str(target_twips))
            # Remove hanging if present
            for attr in [self._qn("w:hangingChars"), self._qn("w:hanging")]:
                if ind.get(attr) is not None:
                    del ind.attrib[attr]
            self.fixes_applied.append({
                "type": "indentation",
                "detail": f"首行缩进: → {expected_chars}字符 ({text_ctx})"
            })

    def _fix_run(self, r_elem, font_rules, is_heading, heading_level, text_ctx):
        rpr = r_elem.find(self._qn("w:rPr"))
        if rpr is None:
            rpr = etree.SubElement(r_elem, self._qn("w:rPr"))
            r_elem.remove(rpr)
            r_elem.insert(0, rpr)

        run_text = "".join(t.text or "" for t in r_elem.findall(self._qn("w:t")))
        if not run_text.strip():
            return

        # Fix font
        expected_cn = font_rules.get("chinese_family", font_rules.get("family", "宋体"))
        expected_en = font_rules.get("english_family", "")
        expected_size = font_rules.get("size_pt", 12)
        expected_bold = font_rules.get("bold", False)

        rfonts = rpr.find(self._qn("w:rFonts"))
        if rfonts is None:
            rfonts = etree.SubElement(rpr, self._qn("w:rFonts"))

        # Fix Chinese font
        current_ea = rfonts.get(self._qn("w:eastAsia"), "")
        if expected_cn and current_ea != expected_cn:
            rfonts.set(self._qn("w:eastAsia"), expected_cn)
            self.fixes_applied.append({
                "type": "font_cn",
                "detail": f"中文字体: {current_ea or 'none'} → {expected_cn} ({text_ctx})"
            })

        # Fix English font - capture old value before modifying
        if expected_en:
            old_ascii = rfonts.get(self._qn("w:ascii"), "")
            changed = False
            for attr in ["w:ascii", "w:hAnsi", "w:cs"]:
                current = rfonts.get(self._qn(attr), "")
                if current != expected_en:
                    rfonts.set(self._qn(attr), expected_en)
                    changed = True
            if changed:
                self.fixes_applied.append({
                    "type": "font_en",
                    "detail": f"英文字体: {old_ascii or 'none'} → {expected_en} ({text_ctx})"
                })

        # Fix font size
        sz = rpr.find(self._qn("w:sz"))
        if sz is not None:
            try:
                current_pt = int(sz.get(self._qn("w:val"), 0)) / 2.0
                if abs(current_pt - expected_size) > 0.5:
                    sz.set(self._qn("w:val"), str(int(expected_size * 2)))
                    sz_cs = rpr.find(self._qn("w:szCs"))
                    if sz_cs is not None:
                        sz_cs.set(self._qn("w:val"), str(int(expected_size * 2)))
                    self.fixes_applied.append({
                        "type": "font_size",
                        "detail": f"字号: {current_pt}pt → {expected_size}pt ({text_ctx})"
                    })
            except (ValueError, TypeError):
                pass

        # Fix bold (headings only)
        if expected_bold:
            bold_elem = rpr.find(self._qn("w:b"))
            if bold_elem is None:
                etree.SubElement(rpr, self._qn("w:b"))
                self.fixes_applied.append({
                    "type": "bold",
                    "detail": f"设置粗体 ({text_ctx})"
                })

        # Fix color (headings should be black)
        if is_heading:
            color = rpr.find(self._qn("w:color"))
            if color is not None:
                current_color = color.get(self._qn("w:val"), "")
                if current_color and current_color.upper() != "000000":
                    color.set(self._qn("w:val"), "000000")
                    self.fixes_applied.append({
                        "type": "color",
                        "detail": f"标题颜色: {current_color} → 000000 ({text_ctx})"
                    })

    def _fix_table(self, tbl):
        """Fix table formatting to three-line style."""
        tbl_pr = tbl.find(self._qn("w:tblPr"))
        if tbl_pr is None:
            return

        borders = tbl_pr.find(self._qn("w:tblBorders"))
        if borders is None:
            borders = etree.SubElement(tbl_pr, self._qn("w:tblBorders"))

        table_rules = self.rules.get("table", {})
        if table_rules.get("border_style") != "three_line":
            return

        border_config = {
            "top": {"val": "single", "sz": "12", "color": "000000"},
            "bottom": {"val": "single", "sz": "12", "color": "000000"},
            "insideH": {"val": "single", "sz": "6", "color": "000000"},
            "left": {"val": "none", "sz": "0", "color": "auto"},
            "right": {"val": "none", "sz": "0", "color": "auto"},
            "insideV": {"val": "none", "sz": "0", "color": "auto"},
        }

        for name, cfg in border_config.items():
            elem = borders.find(self._qn(f"w:{name}"))
            if elem is None:
                elem = etree.SubElement(borders, self._qn(f"w:{name}"))
            for attr, val in cfg.items():
                elem.set(self._qn(f"w:{attr}"), val)

        # Fix table cell fonts
        header_font = table_rules.get("header_font", "黑体")
        body_font = table_rules.get("body_font", "宋体")
        header_size = table_rules.get("header_size_pt", 10.5)
        body_size = table_rules.get("body_size_pt", 10.5)

        rows = tbl.findall(self._qn("w:tr"))
        for r_idx, tr in enumerate(rows):
            is_header = (r_idx == 0)
            font = header_font if is_header else body_font
            size = header_size if is_header else body_size

            for tc in tr.findall(self._qn("w:tc")):
                for p in tc.findall(self._qn("w:p")):
                    for r in p.findall(self._qn("w:r")):
                        rpr = r.find(self._qn("w:rPr"))
                        if rpr is None:
                            rpr = etree.SubElement(r, self._qn("w:rPr"))
                            r.remove(rpr)
                            r.insert(0, rpr)

                        rfonts = rpr.find(self._qn("w:rFonts"))
                        if rfonts is None:
                            rfonts = etree.SubElement(rpr, self._qn("w:rFonts"))

                        rfonts.set(self._qn("w:eastAsia"), font)
                        rfonts.set(self._qn("w:ascii"), font)
                        rfonts.set(self._qn("w:hAnsi"), font)

                        sz = rpr.find(self._qn("w:sz"))
                        if sz is None:
                            sz = etree.SubElement(rpr, self._qn("w:sz"))
                        sz.set(self._qn("w:val"), str(int(size * 2)))

                        if is_header:
                            bold = rpr.find(self._qn("w:b"))
                            if bold is None:
                                etree.SubElement(rpr, self._qn("w:b"))

    def _read_styles_from_data(self):
        """Read styles from the DOCX file."""
        styles = {}
        try:
            with zipfile.ZipFile(self.docx_path, "r") as zf:
                data = zf.read("word/styles.xml")
                root = etree.fromstring(data)
                for style_elem in root.findall(self._qn("w:style")):
                    sid = style_elem.get(self._qn("w:styleId"), "")
                    name_elem = style_elem.find(self._qn("w:name"))
                    name = name_elem.get(self._qn("w:val"), "") if name_elem is not None else ""
                    styles[sid] = {"name": name}
        except Exception:
            pass
        return styles
