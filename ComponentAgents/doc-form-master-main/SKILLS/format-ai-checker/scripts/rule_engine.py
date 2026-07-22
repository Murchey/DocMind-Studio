"""Rule engine - loads rules and checks DOCX XML data against them."""
import re
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None


class RuleEngine:
    """Load rules from YAML and check document compliance."""
    
    def __init__(self, rules_path=None):
        if rules_path is None:
            rules_path = Path(__file__).parent.parent / "rules" / "chinese_academic_rules.yaml"
        self.rules = self._load_rules(rules_path)
        self.issues = []
    
    def _load_rules(self, path):
        path = Path(path)
        if not path.exists():
            return {}
        if yaml:
            with open(path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f)
        else:
            return self._parse_yaml_simple(path)
    
    def _parse_yaml_simple(self, path):
        """Minimal YAML parser for flat key-value rules (no PyYAML dependency)."""
        rules = {}
        with open(path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        
        stack = [rules]
        indent_stack = [-1]
        
        for line in lines:
            stripped = line.rstrip()
            if not stripped or stripped.lstrip().startswith("#"):
                continue
            
            indent = len(line) - len(line.lstrip())
            
            while indent <= indent_stack[-1]:
                stack.pop()
                indent_stack.pop()
            
            if ":" in stripped:
                key, _, val = stripped.lstrip().partition(":")
                key = key.strip()
                val = val.strip()
                
                if val == "" or val == "|":
                    # Child block
                    new_dict = {}
                    stack[-1][key] = new_dict
                    stack.append(new_dict)
                    indent_stack.append(indent)
                else:
                    # Parse value
                    parsed = self._parse_value(val)
                    stack[-1][key] = parsed
        
        return rules
    
    def _parse_value(self, val):
        """Parse a YAML value to Python type."""
        if val.startswith('"') and val.endswith('"'):
            return val[1:-1]
        if val.startswith("'") and val.endswith("'"):
            return val[1:-1]
        if val.lower() == "true":
            return True
        if val.lower() == "false":
            return False
        if val.lower() == "null":
            return None
        try:
            if "." in val:
                return float(val)
            return int(val)
        except ValueError:
            return val
    
    def check_all(self, doc_data):
        """Run all rules against document data. Returns list of issues."""
        self.issues = []
        
        self._check_page(doc_data)
        self._check_fonts(doc_data)
        self._check_paragraphs(doc_data)
        self._check_tables(doc_data)
        self._check_structure(doc_data)
        
        return self.issues
    
    def _add_issue(self, category, severity, rule, expected, actual, location="", suggestion=""):
        self.issues.append({
            "category": category,
            "severity": severity,
            "rule": rule,
            "expected": str(expected),
            "actual": str(actual),
            "location": location,
            "suggestion": suggestion
        })
    
    def _check_page(self, doc_data):
        """Check page size and margins."""
        page_rules = self.rules.get("page", {})
        section = doc_data.get("section", {})
        
        # Page size
        size_rules = page_rules.get("size", {})
        page_size = section.get("page_size", {})
        if page_size:
            w = page_size.get("w", 0)
            h = page_size.get("h", 0)
            expected_w = size_rules.get("width_mm", 210)
            expected_h = size_rules.get("height_mm", 297)
            
            actual_w_cm = w
            actual_h_cm = h
            
            if abs(actual_w_cm - expected_w / 10) > 0.5 or abs(actual_h_cm - expected_h / 10) > 0.5:
                self._add_issue(
                    "page_layout", size_rules.get("severity", "critical"),
                    f"页面尺寸应为 {expected_w}x{expected_h}mm",
                    f"{expected_w}x{expected_h}mm",
                    f"{actual_w_cm*10:.0f}x{actual_h_cm*10:.0f}mm",
                    "文档节属性",
                    "调整页面尺寸为 A4"
                )
        
        # Margins
        margin_rules = page_rules.get("margins", {})
        margins = section.get("margins", {})
        if margins:
            margin_map = {
                "top": ("top_cm", "上边距"),
                "bottom": ("bottom_cm", "下边距"),
                "left": ("left_cm", "左边距"),
                "right": ("right_cm", "右边距")
            }
            for key, (rule_key, label) in margin_map.items():
                expected = margin_rules.get(rule_key, 0)
                actual = margins.get(key, 0)
                if actual and abs(actual - expected) > 0.3:
                    self._add_issue(
                        "page_layout", margin_rules.get("severity", "critical"),
                        f"{label}应为 {expected}cm",
                        f"{expected}cm",
                        f"{actual:.2f}cm",
                        "文档节属性",
                        f"调整{label}为 {expected}cm"
                    )
    
    def _check_fonts(self, doc_data):
        """Check font assignments for all runs."""
        font_rules = self.rules.get("fonts", {})
        paragraphs = doc_data.get("paragraphs", [])
        
        for para in paragraphs:
            style_id = para.get("style_id", "")
            text = para.get("text", "")
            
            if para.get("is_empty") or para.get("has_formula"):
                continue
            
            # Determine which font rule applies
            applicable_rule = None
            for rule_name, rule_def in font_rules.items():
                applies_to = rule_def.get("applies_to", [])
                # Case-insensitive check against applies_to list
                if any(style_id.lower() == a.lower() for a in applies_to) or \
                   self._matches_style_category(style_id, rule_name):
                    applicable_rule = rule_def
                    break
            
            # Heading4+ gets the highest available heading rule (heading3)
            if applicable_rule is None and style_id.lower().startswith("heading"):
                try:
                    level = int(style_id[-1])
                except (ValueError, IndexError):
                    level = 0
                # Try heading3, heading2, heading1 in order (highest first)
                for fallback in ["heading3", "heading2", "heading1"]:
                    if fallback in font_rules:
                        applicable_rule = font_rules[fallback]
                        break
            
            if applicable_rule is None:
                applicable_rule = font_rules.get("body", {})
            
            # Check each run's font
            for run in para.get("runs", []):
                run_text = run.get("text", "")
                if not run_text.strip():
                    continue
                
                rpr = run.get("rPr", {})
                font_info = rpr.get("font", {})
                size_pt = rpr.get("size_pt")
                bold = rpr.get("bold", False)
                color = rpr.get("color", "")
                
                # Check Chinese font
                cn_font = font_info.get("eastAsia", "")
                expected_cn = applicable_rule.get("chinese_family", applicable_rule.get("family", ""))
                if cn_font and expected_cn and cn_font != expected_cn:
                    self._add_issue(
                        "font", applicable_rule.get("severity", "warning"),
                        f"中文字体应为 {expected_cn}",
                        expected_cn, cn_font,
                        f"段落 {para['index']+1}: \"{run_text[:20]}...\"",
                        f"将字体从 {cn_font} 改为 {expected_cn}"
                    )
                
                # Check English font
                en_font = font_info.get("ascii", "")
                expected_en = applicable_rule.get("english_family", "")
                if en_font and expected_en and en_font != expected_en:
                    self._add_issue(
                        "font", applicable_rule.get("severity", "warning"),
                        f"英文字体应为 {expected_en}",
                        expected_en, en_font,
                        f"段落 {para['index']+1}: \"{run_text[:20]}...\"",
                        f"将字体从 {en_font} 改为 {expected_en}"
                    )
                
                # Check font size
                expected_size = applicable_rule.get("size_pt", 12)
                if size_pt and abs(size_pt - expected_size) > 0.5:
                    self._add_issue(
                        "font", applicable_rule.get("severity", "critical"),
                        f"字号应为 {expected_size}pt",
                        f"{expected_size}pt", f"{size_pt}pt",
                        f"段落 {para['index']+1}: \"{run_text[:20]}...\"",
                        f"将字号从 {size_pt}pt 改为 {expected_size}pt"
                    )
                
                # Check bold for headings
                expected_bold = applicable_rule.get("bold", False)
                if expected_bold and not bold and style_id.startswith("Heading"):
                    self._add_issue(
                        "font", applicable_rule.get("severity", "warning"),
                        "标题应为粗体",
                        "粗体", "非粗体",
                        f"段落 {para['index']+1}: \"{run_text[:20]}...\"",
                        "设置字体为粗体"
                    )
    
    def _matches_style_category(self, style_id, rule_name):
        """Check if a style ID maps to a rule category."""
        if not style_id:
            return False
        
        sid_lower = style_id.lower()
        
        # Heading styles: Heading1 -> heading1, Heading2 -> heading2, etc.
        if rule_name.startswith("heading"):
            level = rule_name.replace("heading", "")
            if sid_lower == f"heading{level}" or sid_lower == f"heading {level}":
                return True
            # Heading4+ falls through to the highest available heading rule
            # (Heading4 gets heading3 rules as closest match)
            return False
        
        # Body and other categories - case-insensitive substring match
        mapping = {
            "body": ["Normal", "Body", "BodyText", "FirstParagraph", "Compact",
                     "body_text", "first_paragraph"],
        }
        candidates = mapping.get(rule_name, [])
        return any(c.lower() in sid_lower for c in candidates)
    
    def _check_paragraphs(self, doc_data):
        """Check paragraph formatting (alignment, spacing, indentation)."""
        para_rules = self.rules.get("paragraph", {})
        heading_rules = self.rules.get("heading", {})
        paragraphs = doc_data.get("paragraphs", [])
        
        for para in paragraphs:
            if para.get("is_empty") or para.get("has_formula"):
                continue
            
            style_id = para.get("style_id", "")
            ppr = para.get("effective_pPr", {})
            text = para.get("text", "")[:30]
            location = f"段落 {para['index']+1}: \"{text}...\""
            
            # Skip headings for body paragraph rules
            if style_id.startswith("Heading") or style_id.startswith("heading"):
                self._check_heading_paragraph(para, heading_rules)
                continue
            
            # Check alignment
            expected_align = para_rules.get("alignment", "both")
            actual_align = ppr.get("alignment", "")
            if expected_align and actual_align and actual_align != expected_align:
                align_map = {"both": "两端对齐", "center": "居中", "left": "左对齐", "right": "右对齐"}
                self._add_issue(
                    "paragraph", para_rules.get("alignment", {}).get("severity", "critical") if isinstance(para_rules.get("alignment"), dict) else para_rules.get("severity", "critical"),
                    f"段落应为{align_map.get(expected_align, expected_align)}",
                    align_map.get(expected_align, expected_align),
                    align_map.get(actual_align, actual_align),
                    location,
                    f"将对齐方式改为{align_map.get(expected_align, expected_align)}"
                )
            
            # Check line spacing
            spacing_rules = para_rules.get("line_spacing", {})
            expected_line = spacing_rules.get("value", 1.5) if isinstance(spacing_rules, dict) else 1.5
            actual_line = ppr.get("spacing", {}).get("line")
            if actual_line and expected_line and abs(actual_line - expected_line) > 0.1:
                self._add_issue(
                    "paragraph", spacing_rules.get("severity", "critical") if isinstance(spacing_rules, dict) else "critical",
                    f"行距应为 {expected_line} 倍",
                    f"{expected_line}倍", f"{actual_line:.1f}倍",
                    location,
                    f"将行距调整为 {expected_line} 倍"
                )
            
            # Check first line indent
            indent_rules = para_rules.get("first_line_indent", {})
            expected_chars = indent_rules.get("value_chars", 2) if isinstance(indent_rules, dict) else 2
            indent_info = ppr.get("indentation", {})
            actual_chars = indent_info.get("first_line_chars")
            
            has_indent = False
            if actual_chars:
                try:
                    has_indent = int(actual_chars) >= expected_chars * 100
                except (ValueError, TypeError):
                    pass
            
            if not has_indent:
                actual_first_line = indent_info.get("first_line", 0) or 0
                # first_line is in points (twips / 20); 2 chars at 12pt ≈ 24 points
                if actual_first_line < 20:
                    self._add_issue(
                        "paragraph", indent_rules.get("severity", "critical") if isinstance(indent_rules, dict) else "critical",
                        f"首行应缩进 {expected_chars} 字符",
                        f"{expected_chars} 字符",
                        f"无缩进或缩进不足",
                        location,
                        f"设置首行缩进为 {expected_chars} 字符"
                    )
    
    def _check_heading_paragraph(self, para, heading_rules):
        """Check heading-specific formatting."""
        style_id = para.get("style_id", "")
        ppr = para.get("effective_pPr", {})
        text = para.get("text", "")[:30]
        location = f"标题段落 {para['index']+1}: \"{text}...\""
        
        # Determine heading level (supports any level, not just 1-3)
        level = None
        try:
            # Extract the numeric part from style_id (e.g., "Heading4" -> 4)
            level = int(style_id[-1])
        except (ValueError, IndexError):
            for i in range(1, 10):
                if f"Heading{i}" in style_id or f"heading{i}" in style_id:
                    level = i
                    break
        
        if level is None:
            return
        
        level_key = f"level{level}"
        level_rules = heading_rules.get(level_key, {})
        if not level_rules:
            return
        
        # Check alignment
        expected_align = level_rules.get("alignment", "left")
        actual_align = ppr.get("alignment", "")
        if expected_align and actual_align and actual_align != expected_align:
            self._add_issue(
                "heading", level_rules.get("severity", "warning"),
                f"H{level} 标题应为{expected_align}",
                expected_align, actual_align,
                location,
                f"调整标题对齐方式"
            )
    
    def _check_tables(self, doc_data):
        """Check table formatting."""
        table_rules = self.rules.get("table", {})
        tables = doc_data.get("tables", [])
        
        for t_idx, table in enumerate(tables):
            borders = table.get("properties", {}).get("borders", {})
            
            # Check three-line table format
            expected_style = table_rules.get("border_style", "three_line")
            if expected_style == "three_line":
                # Three-line: top/bottom should be thick (≥8), insideH thin (≥4), no left/right/insideV
                top_sz = self._get_border_sz(borders, "top")
                bottom_sz = self._get_border_sz(borders, "bottom")
                left_sz = self._get_border_sz(borders, "left")
                right_sz = self._get_border_sz(borders, "right")
                inside_v = self._get_border_sz(borders, "insideV")
                
                if left_sz and int(left_sz) > 0:
                    self._add_issue(
                        "table", table_rules.get("severity", "warning"),
                        "三线表不应有左右边框",
                        "无左右边框", f"左边框 sz={left_sz}",
                        f"表格 {t_idx+1}",
                        "移除左右边框"
                    )
                
                if inside_v and int(inside_v) > 0:
                    self._add_issue(
                        "table", table_rules.get("severity", "warning"),
                        "三线表不应有竖线",
                        "无竖线", f"内部竖线 sz={inside_v}",
                        f"表格 {t_idx+1}",
                        "移除内部竖线"
                    )
            
            # Check table font
            header_font = table_rules.get("header_font", "黑体")
            body_font = table_rules.get("body_font", "宋体")
            
            for r_idx, row in enumerate(table.get("rows", [])):
                is_header = (r_idx == 0)
                expected = header_font if is_header else body_font
                
                for cell in row:
                    for para in cell:
                        for run in para.get("runs", []):
                            rpr = run.get("rPr", {})
                            font_info = rpr.get("font", {})
                            actual = font_info.get("eastAsia", "")
                            if actual and actual != expected:
                                self._add_issue(
                                    "table", table_rules.get("severity", "warning"),
                                    f"表格{'表头' if is_header else '表体'}字体应为 {expected}",
                                    expected, actual,
                                    f"表格 {t_idx+1} 第{r_idx+1}行",
                                    f"将字体改为 {expected}"
                                )
    
    def _get_border_sz(self, borders, name):
        border = borders.get(name, {})
        return border.get("sz", "0") if border else "0"
    
    def _check_structure(self, doc_data):
        """Check document structure rules."""
        struct_rules = self.rules.get("structure", {})
        paragraphs = doc_data.get("paragraphs", [])
        
        if not paragraphs:
            return
        
        # Check consecutive empty paragraphs
        max_empty = struct_rules.get("consecutive_empty_paragraphs", {}).get("max_allowed", 2)
        empty_count = 0
        for para in paragraphs:
            if para.get("is_empty"):
                empty_count += 1
                if empty_count > max_empty:
                    self._add_issue(
                        "structure", struct_rules.get("consecutive_empty_paragraphs", {}).get("severity", "warning"),
                        f"连续空段落不超过 {max_empty} 个",
                        f"最多 {max_empty} 个", f"超过 {max_empty} 个连续空段落",
                        f"段落 {para['index']+1} 附近",
                        "删除多余空段落"
                    )
                    break
            else:
                empty_count = 0
        
        # Check heading numbering
        numbering_rules = struct_rules.get("heading_numbering", {})
        if numbering_rules.get("required", False):
            patterns = numbering_rules.get("patterns", {})
            h1_found = False
            for para in paragraphs:
                if para.get("style_id", "").startswith("Heading") and para.get("text"):
                    text = para.get("text", "")
                    # Check if first H1 has numbering
                    if "Heading1" in para.get("style_id", ""):
                        pattern = patterns.get("h1", "")
                        if pattern and not re.match(pattern, text):
                            self._add_issue(
                                "structure", numbering_rules.get("severity", "warning"),
                                f"H1 标题应匹配编号格式: {pattern}",
                                pattern, text[:30],
                                f"段落 {para['index']+1}",
                                "添加章编号（如 '第一章 xxx'）"
                            )
                        h1_found = True
        
        # Check for references section
        ref_rules = struct_rules.get("has_references", {})
        if ref_rules.get("required", False):
            ref_patterns = ref_rules.get("patterns", ["参考文献"])
            has_ref = False
            for para in paragraphs[-10:]:  # Check last 10 paragraphs
                text = para.get("text", "")
                if any(p in text for p in ref_patterns):
                    has_ref = True
                    break
            if not has_ref:
                self._add_issue(
                    "structure", ref_rules.get("severity", "warning"),
                    "文档应包含参考文献部分",
                    "有参考文献", "未找到参考文献",
                    "文档末尾",
                    "添加参考文献部分"
                )
