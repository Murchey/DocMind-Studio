"""DOCX XML reader - extracts all formatting attributes from DOCX XML internals."""
import zipfile
import re
from pathlib import Path
from lxml import etree

WML_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"

class DocxXmlReader:
    """Read DOCX as ZIP of XML, extract every formatting attribute."""
    
    def __init__(self, docx_path):
        self.docx_path = Path(docx_path)
        self._ns = {"w": WML_NS}
        self._styles_cache = None
    
    def _open_zip(self):
        return zipfile.ZipFile(self.docx_path, 'r')
    
    def _read_xml(self, zip_file, name):
        """Read and parse an XML file from the ZIP."""
        try:
            data = zip_file.read(name)
            return etree.fromstring(data)
        except (KeyError, etree.XMLSyntaxError):
            return None
    
    def _qn(self, tag):
        """Expand namespace prefix to Clark notation."""
        prefix, local = tag.split(":")
        return "{%s}%s" % (self._ns[prefix], local)
    
    def _get_text(self, elem):
        """Get all text content from an element and its children."""
        return "".join(elem.itertext()).strip()
    
    def _parse_twbips(self, val):
        """Parse twentieths of a point (twips) to points."""
        try:
            return int(val) / 20.0
        except (ValueError, TypeError):
            return None
    
    def _parse_emu(self, val):
        """Parse twips (twentieths of a point) to centimeters.
        Note: OOXML sectPr uses twips, not EMUs. 1 inch = 1440 twips = 2.54 cm.
        """
        try:
            twips = int(val)
            return twips * 2.54 / 1440.0
        except (ValueError, TypeError):
            return None
    
    def _parse_half_pt(self, val):
        """Parse half-point value to points."""
        try:
            return int(val) / 2.0
        except (ValueError, TypeError):
            return None
    
    def _parse_line_spacing(self, val):
        """Parse line spacing value (240 = single)."""
        try:
            return int(val) / 240.0
        except (ValueError, TypeError):
            return None
    
    def read_styles(self):
        """Read all style definitions from word/styles.xml."""
        if self._styles_cache is not None:
            return self._styles_cache
        
        styles = {}
        with self._open_zip() as zf:
            root = self._read_xml(zf, "word/styles.xml")
            if root is None:
                return styles
            
            for style_elem in root.findall(self._qn("w:style")):
                style_id = style_elem.get(self._qn("w:styleId"), "")
                style_type = style_elem.get(self._qn("w:type"), "")
                style_name = ""
                
                name_elem = style_elem.find(self._qn("w:name"))
                if name_elem is not None:
                    style_name = name_elem.get(self._qn("w:val"), "")
                
                info = {
                    "id": style_id,
                    "type": style_type,
                    "name": style_name,
                    "pPr": self._parse_ppr(style_elem.find(self._qn("w:pPr"))),
                    "rPr": self._parse_rpr(style_elem.find(self._qn("w:rPr")))
                }
                styles[style_id] = info
        
        self._styles_cache = styles
        return styles
    
    def _parse_ppr(self, ppr_elem):
        """Parse paragraph properties element."""
        if ppr_elem is None:
            return {}
        
        info = {}
        
        # Alignment
        jc = ppr_elem.find(self._qn("w:jc"))
        if jc is not None:
            info["alignment"] = jc.get(self._qn("w:val"), "")
        
        # Spacing
        spacing = ppr_elem.find(self._qn("w:spacing"))
        if spacing is not None:
            info["spacing"] = {
                "before": self._parse_twbips(spacing.get(self._qn("w:before"))),
                "after": self._parse_twbips(spacing.get(self._qn("w:after"))),
                "line": self._parse_line_spacing(spacing.get(self._qn("w:line"))),
                "line_rule": spacing.get(self._qn("w:lineRule"), "")
            }
        
        # Indentation
        ind = ppr_elem.find(self._qn("w:ind"))
        if ind is not None:
            info["indentation"] = {
                "first_line_chars": ind.get(self._qn("w:firstLineChars")),
                "first_line": self._parse_twbips(ind.get(self._qn("w:firstLine"))),
                "left_chars": ind.get(self._qn("w:leftChars")),
                "left": self._parse_twbips(ind.get(self._qn("w:left"))),
                "hanging_chars": ind.get(self._qn("w:hangingChars")),
                "hanging": self._parse_twbips(ind.get(self._qn("w:hanging")))
            }
        
        # Style reference
        pstyle = ppr_elem.find(self._qn("w:pStyle"))
        if pstyle is not None:
            info["style_id"] = pstyle.get(self._qn("w:val"), "")
        
        # Keep with next
        keep_next = ppr_elem.find(self._qn("w:keepNext"))
        if keep_next is not None:
            info["keep_next"] = True
        
        # Page break before
        page_break = ppr_elem.find(self._qn("w:pageBreakBefore"))
        if page_break is not None:
            info["page_break_before"] = True
        
        return info
    
    def _parse_rpr(self, rpr_elem):
        """Parse run properties element."""
        if rpr_elem is None:
            return {}
        
        info = {}
        
        # Font
        rfonts = rfonts_elem = rpr_elem.find(self._qn("w:rFonts"))
        if rfonts is not None:
            info["font"] = {
                "ascii": rfonts.get(self._qn("w:ascii"), ""),
                "hAnsi": rfonts.get(self._qn("w:hAnsi"), ""),
                "eastAsia": rfonts.get(self._qn("w:eastAsia"), ""),
                "cs": rfonts.get(self._qn("w:cs"), "")
            }
        
        # Font size
        sz = rpr_elem.find(self._qn("w:sz"))
        if sz is not None:
            info["size_pt"] = self._parse_half_pt(sz.get(self._qn("w:val")))
        
        sz_cs = rpr_elem.find(self._qn("w:szCs"))
        if sz_cs is not None:
            info["size_cs_pt"] = self._parse_half_pt(sz_cs.get(self._qn("w:val")))
        
        # Bold
        bold = rpr_elem.find(self._qn("w:b"))
        if bold is not None:
            val = bold.get(self._qn("w:val"), "true")
            info["bold"] = val.lower() != "false"
        else:
            info["bold"] = False
        
        # Color
        color = rpr_elem.find(self._qn("w:color"))
        if color is not None:
            info["color"] = color.get(self._qn("w:val"), "")
        
        # Italic
        italic = rpr_elem.find(self._qn("w:i"))
        if italic is not None:
            val = italic.get(self._qn("w:val"), "true")
            info["italic"] = val.lower() != "false"
        else:
            info["italic"] = False
        
        # Underline
        underline = rpr_elem.find(self._qn("w:u"))
        if underline is not None:
            info["underline"] = underline.get(self._qn("w:val"), "")
        
        return info
    
    def read_document(self):
        """Read document.xml and extract all paragraphs with full formatting."""
        paragraphs = []
        tables = []
        section_info = {}
        
        with self._open_zip() as zf:
            root = self._read_xml(zf, "word/document.xml")
            if root is None:
                return {"paragraphs": [], "tables": [], "section": {}}
            
            body = root.find(self._qn("w:body"))
            if body is None:
                return {"paragraphs": [], "tables": [], "section": {}}
            
            # Read styles for resolving style hierarchy
            styles = self.read_styles()
            
            # Process body children in order
            para_idx = 0
            for child in body:
                tag = etree.QName(child).localname
                
                if tag == "p":
                    para = self._parse_paragraph(child, styles, para_idx)
                    paragraphs.append(para)
                    para_idx += 1
                
                elif tag == "tbl":
                    table = self._parse_table(child, styles)
                    tables.append(table)
                
                elif tag == "sectPr":
                    section_info = self._parse_section(child)
            
            # Detect page break before paragraphs (for page counting)
            # Each w:lastRenderedPageBreak or sectPr implies a page break
            page_breaks = 0
            for p_elem in body.findall(self._qn("w:p")):
                ppr = p_elem.find(self._qn("w:pPr"))
                if ppr is not None and ppr.find(self._qn("w:pageBreakBefore")) is not None:
                    page_breaks += 1
                for run in p_elem.findall(self._qn("w:r")):
                    for br in run.findall(self._qn("w:br")):
                        if br.get(self._qn("w:type")) == "page":
                            page_breaks += 1
        
        return {
            "paragraphs": paragraphs,
            "tables": tables,
            "section": section_info,
            "estimated_pages": max(1, page_breaks + 1)
        }
    
    def _parse_paragraph(self, p_elem, styles, idx):
        """Parse a single paragraph element with all formatting."""
        ppr = p_elem.find(self._qn("w:pPr"))
        raw_pPr = self._parse_ppr(ppr)
        
        # Resolve effective formatting (style + direct formatting)
        style_id = raw_pPr.get("style_id", "")
        style_def = styles.get(style_id, {})
        
        # Merge: direct formatting overrides style definition
        effective_pPr = self._merge_ppr(style_def.get("pPr", {}), raw_pPr)
        
        # Extract runs
        runs = []
        text_parts = []
        has_formula = False
        has_image = False
        
        for r_elem in p_elem.findall(self._qn("w:r")):
            rpr = r_elem.find(self._qn("w:rPr"))
            raw_rPr = self._parse_rpr(rpr)
            
            # Get text
            text = ""
            for t in r_elem.findall(self._qn("w:t")):
                text += (t.text or "")
            
            # Check for images
            drawings = r_elem.findall(".//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}drawing")
            if not drawings:
                drawings = r_elem.findall(".//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}pict")
            if drawings:
                has_image = True
            
            # Check for formulas (oMath)
            for child in r_elem:
                local = etree.QName(child).localname
                ns = etree.QName(child).namespace or ""
                if local == "oMath" or "math" in ns.lower():
                    has_formula = True
                    break
            
            runs.append({
                "text": text,
                "rPr": raw_rPr
            })
            text_parts.append(text)
        
        full_text = "".join(text_parts)
        
        return {
            "index": idx,
            "text": full_text,
            "text_length": len(full_text),
            "style_id": style_id,
            "style_name": style_def.get("name", ""),
            "effective_pPr": effective_pPr,
            "runs": runs,
            "has_formula": has_formula,
            "has_image": has_image,
            "is_empty": len(full_text.strip()) == 0 and not has_image and not has_formula
        }
    
    def _parse_table(self, tbl_elem, styles):
        """Parse a table element."""
        rows = []
        for tr in tbl_elem.findall(self._qn("w:tr")):
            cells = []
            for tc in tr.findall(self._qn("w:tc")):
                cell_paras = []
                for p in tc.findall(self._qn("w:p")):
                    para = self._parse_paragraph(p, styles, -1)
                    cell_paras.append(para)
                cells.append(cell_paras)
            rows.append(cells)
        
        # Table properties
        tbl_pr = tbl_elem.find(self._qn("w:tblPr"))
        tbl_info = {}
        if tbl_pr is not None:
            borders = tbl_pr.find(self._qn("w:tblBorders"))
            if borders is not None:
                border_info = {}
                for border_name in ["top", "bottom", "left", "right", "insideH", "insideV"]:
                    border_elem = borders.find(self._qn("w:" + border_name))
                    if border_elem is not None:
                        border_info[border_name] = {
                            "val": border_elem.get(self._qn("w:val"), ""),
                            "sz": border_elem.get(self._qn("w:sz"), ""),
                            "color": border_elem.get(self._qn("w:color"), "")
                        }
                tbl_info["borders"] = border_info
        
        return {
            "rows": rows,
            "row_count": len(rows),
            "col_count": max((len(r) for r in rows), default=0),
            "properties": tbl_info
        }
    
    def _parse_section(self, sect_pr):
        """Parse section properties (page size, margins)."""
        info = {}
        
        pg_sz = sect_pr.find(self._qn("w:pgSz"))
        if pg_sz is not None:
            info["page_size"] = {
                "w": self._parse_emu(pg_sz.get(self._qn("w:w"))),
                "h": self._parse_emu(pg_sz.get(self._qn("w:h"))),
                "orient": pg_sz.get(self._qn("w:orient"), "portrait")
            }
        
        pg_mar = sect_pr.find(self._qn("w:pgMar"))
        if pg_mar is not None:
            info["margins"] = {
                "top": self._parse_emu(pg_mar.get(self._qn("w:top"))),
                "bottom": self._parse_emu(pg_mar.get(self._qn("w:bottom"))),
                "left": self._parse_emu(pg_mar.get(self._qn("w:left"))),
                "right": self._parse_emu(pg_mar.get(self._qn("w:right"))),
                "header": self._parse_emu(pg_mar.get(self._qn("w:header"))),
                "footer": self._parse_emu(pg_mar.get(self._qn("w:footer")))
            }
        
        # Check for header/footer references
        header_refs = sect_pr.findall(self._qn("w:headerReference"))
        footer_refs = sect_pr.findall(self._qn("w:footerReference"))
        info["has_header"] = len(header_refs) > 0
        info["has_footer"] = len(footer_refs) > 0
        
        # Page number start
        pg_num = sect_pr.find(self._qn("w:pgNumType"))
        if pg_num is not None:
            info["page_num_start"] = pg_num.get(self._qn("w:start"))
        
        return info
    
    def _merge_ppr(self, style_ppr, direct_pPr):
        """Merge style paragraph properties with direct formatting."""
        merged = dict(style_ppr)
        for key, val in direct_pPr.items():
            if val is not None and val != {} and val != "":
                merged[key] = val
        return merged
