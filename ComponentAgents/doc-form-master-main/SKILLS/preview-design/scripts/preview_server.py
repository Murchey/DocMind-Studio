import json
import socket
import webbrowser
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse, parse_qs

DEFAULT_TEMPLATE = {
    "paper_type": "chinese_academic",
    "fonts": {
        "chinese": {"family": "宋体", "size": 12},
        "english": {"family": "Times New Roman", "size": 12},
        "heading": {"family": "黑体"}
    },
    "heading": {
        "level1": {"font": "黑体", "size": 16, "bold": True, "alignment": "center", "color": "#000000", "spacing_before": 24, "spacing_after": 18},
        "level2": {"font": "黑体", "size": 14, "bold": True, "alignment": "left", "color": "#000000", "spacing_before": 18, "spacing_after": 12},
        "level3": {"font": "黑体", "size": 13, "bold": True, "alignment": "left", "color": "#000000", "spacing_before": 12, "spacing_after": 6}
    },
    "paragraph": {"alignment": "justify", "line_spacing": 1.5, "first_indent": 2, "paragraph_spacing": False},
    "page": {"margin_top": 2.54, "margin_bottom": 2.54, "margin_left": 3.18, "margin_right": 3.18},
    "toc": {"enabled": False, "title": "目  录", "title_font": "黑体", "title_size": 16, "entry_font": "宋体", "entry_size": 12, "max_level": 3, "indent_step": 2, "dot_leaders": True},
    "header": {"enabled": False, "text": "", "font": "宋体", "size": 9, "alignment": "center", "separator_line": True},
    "footer": {"enabled": False, "page_number_format": "arabic", "font": "宋体", "size": 9, "alignment": "center"},
    "cover": {
        "enabled": False,
        "title": {
            "text": "课程作业",
            "font": "黑体",
            "size": 22,
            "bold": True,
            "alignment": "center",
            "color": "#000000"
        },
        "info_items": [
            {"label": "学号", "value": "", "font": "宋体", "size": 14},
            {"label": "姓名", "value": "", "font": "宋体", "size": 14},
            {"label": "学院", "value": "", "font": "宋体", "size": 14},
            {"label": "专业", "value": "", "font": "宋体", "size": 14},
            {"label": "指导教师", "value": "", "font": "宋体", "size": 14},
            {"label": "日期", "value": "", "font": "宋体", "size": 14}
        ],
        "logo": {
            "enabled": False,
            "image_data": "",
            "width": 120,
            "height": 120,
            "position": "top"
        },
        "layout": {
            "vertical_align": "center",
            "spacing_after_title": 60,
            "spacing_between_items": 10
        }
    }
}


class PreviewState:
    def __init__(self, ast_path, template_config_path, source_docx_path=None):
        self.ast_path = Path(ast_path)
        self.template_config_path = Path(template_config_path)
        self.source_docx_path = Path(source_docx_path) if source_docx_path else None
        self.ast = self._load_json(self.ast_path)
        self.template_config = self._load_json(self.template_config_path)
        self.confirmed = False
        self.edited_config = None
        self.cover_preserved = True
        self.toc_preserved = True
        # Note annotation state
        self.notes = []
        self.page_comments = []

    @staticmethod
    def _load_json(path):
        if path and Path(path).exists():
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def get_cover_paras(self):
        return [p for p in self.ast.get("paragraphs", []) if p.get("section") == "cover"]

    def get_toc_paras(self):
        return [p for p in self.ast.get("paragraphs", []) if p.get("section") == "toc"]

    def get_body_sample(self):
        body = [p for p in self.ast.get("paragraphs", []) if p.get("section") == "body"]
        return body[:30]

    def get_all_headings(self):
        headings = []
        for p in self.ast.get("paragraphs", []):
            style = p.get("style") or ""
            text = p.get("text", "").strip()
            if "Heading" in style and text:
                level = 1
                if "Heading 2" in style or "heading 2" in style.lower():
                    level = 2
                elif "Heading 3" in style or "heading 3" in style.lower():
                    level = 3
                headings.append({"text": text, "level": level})
        return headings

    def has_cover(self):
        return len(self.get_cover_paras()) > 0

    def has_toc(self):
        return len(self.get_toc_paras()) > 0


STATE = None


def build_preview_html(state):
    cfg = state.template_config or DEFAULT_TEMPLATE
    fonts = cfg.get("fonts", {})
    headings = cfg.get("heading", {})
    para_cfg = cfg.get("paragraph", {})
    page_cfg = cfg.get("page", {})
    toc_cfg = cfg.get("toc", DEFAULT_TEMPLATE["toc"])
    header_cfg = cfg.get("header", DEFAULT_TEMPLATE["header"])
    footer_cfg = cfg.get("footer", DEFAULT_TEMPLATE["footer"])

    h1 = headings.get("level1", {})
    h2 = headings.get("level2", {})
    h3 = headings.get("level3", {})

    chinese_font = fonts.get("chinese", {}).get("family", "宋体")
    english_font = fonts.get("english", {}).get("family", "Times New Roman")
    heading_font = fonts.get("heading", {}).get("family", "黑体")
    body_size = fonts.get("chinese", {}).get("size", 12)
    line_spacing = para_cfg.get("line_spacing", 1.5)
    first_indent = para_cfg.get("first_indent", 2)
    paragraph_spacing = para_cfg.get("paragraph_spacing", False)

    toc_enabled = toc_cfg.get("enabled", False)
    toc_title = toc_cfg.get("title", "目  录")
    toc_title_font = toc_cfg.get("title_font", "黑体")
    toc_title_size = toc_cfg.get("title_size", 16)
    toc_entry_font = toc_cfg.get("entry_font", "宋体")
    toc_entry_size = toc_cfg.get("entry_size", 12)
    toc_max_level = toc_cfg.get("max_level", 3)
    toc_indent_step = toc_cfg.get("indent_step", 2)
    toc_dot_leaders = toc_cfg.get("dot_leaders", True)

    header_enabled = header_cfg.get("enabled", False)
    header_text = header_cfg.get("text", "")
    header_font = header_cfg.get("font", "宋体")
    header_size = header_cfg.get("size", 9)
    header_align = header_cfg.get("alignment", "center")
    header_sep = header_cfg.get("separator_line", True)

    footer_enabled = footer_cfg.get("enabled", False)
    footer_pn_fmt = footer_cfg.get("page_number_format", "arabic")
    footer_font = footer_cfg.get("font", "宋体")
    footer_size = footer_cfg.get("size", 9)
    footer_align = footer_cfg.get("alignment", "center")

    all_headings = state.get_all_headings()

    cover_cfg = cfg.get("cover", DEFAULT_TEMPLATE["cover"])
    cover_enabled = cover_cfg.get("enabled", False)
    cover_title = cover_cfg.get("title", {})
    cover_info_items = cover_cfg.get("info_items", [])
    cover_logo = cover_cfg.get("logo", {})
    cover_layout = cover_cfg.get("layout", {})

    cover_section = ""
    if state.has_cover():
        cover_paras = state.get_cover_paras()
        cover_items = ""
        for i, p in enumerate(cover_paras):
            text = p.get("text", "").strip()
            if text:
                cover_items += f'<div class="cover-item annotatable" data-section="cover" data-idx="{i}" onclick="onAnnotatableClick(this)"><span class="note-badge"></span>{text}</div>'
            else:
                cover_items += f'<div class="cover-item empty annotatable" data-section="cover" data-idx="{i}" onclick="onAnnotatableClick(this)"><span class="note-badge"></span>&nbsp;</div>'
        cover_section = f'''
        <div class="section-block" id="cover-section">
            <h2 class="section-title">封面页 <span class="badge">已检测到</span></h2>
            <div class="cover-preview">{cover_items}</div>
            <div class="control-row">
                <label><input type="checkbox" id="keep-cover" checked> 保留原始封面页设计</label>
            </div>
            <div class="control-row">
                <label><input type="checkbox" id="redesign-cover" onchange="toggleCoverDesign()"> 重新设计封面页</label>
            </div>
        </div>'''
    else:
        cover_section = '''
        <div class="section-block" id="cover-section">
            <h2 class="section-title">封面页 <span class="badge empty">未检测到</span></h2>
            <p class="info-text">文档未检测到封面页。</p>
            <div class="control-row">
                <label><input type="checkbox" id="redesign-cover" onchange="toggleCoverDesign()"> 设计封面页</label>
            </div>
        </div>'''

    toc_existing_section = ""
    if state.has_toc():
        toc_paras = state.get_toc_paras()
        toc_items = ""
        for i, p in enumerate(toc_paras):
            text = p.get("text", "").strip()
            if text:
                toc_items += f'<div class="toc-item annotatable" data-section="toc" data-idx="{i}" onclick="onAnnotatableClick(this)"><span class="note-badge"></span>{text}</div>'
        toc_existing_section = f'''
        <div class="section-block">
            <h2 class="section-title">已有目录页 <span class="badge">已检测到</span></h2>
            <div class="toc-preview">{toc_items}</div>
            <div class="control-row">
                <label><input type="checkbox" id="keep-toc" checked> 保留原始目录页设计</label>
            </div>
        </div>'''
    else:
        toc_existing_section = '''
        <div class="section-block">
            <h2 class="section-title">已有目录页 <span class="badge empty">未检测到</span></h2>
            <p class="info-text">文档未检测到目录页。您可以在下方选择自动生成。</p>
        </div>'''

    toc_heading_preview = ""
    for h in all_headings[:20]:
        indent = (h["level"] - 1) * toc_indent_step
        dots = " · · · · · · · · · ·" if toc_dot_leaders else ""
        toc_heading_preview += f'<div style="padding:2px 0;font-size:{toc_entry_size}pt;font-family:{toc_entry_font};margin-left:{indent}em;">{h["text"]}<span style="color:#aaa;">{dots}</span></div>'
    if not all_headings:
        toc_heading_preview = '<div style="color:#999;font-size:12px;">未检测到标题，无法自动生成目录</div>'

    header_preview = ""
    if header_enabled:
        sep_style = "border-bottom:1px solid #333;padding-bottom:4px;" if header_sep else ""
        header_preview = f'<div style="font-size:{header_size}pt;font-family:{header_font};text-align:{header_align};{sep_style}">{header_text if header_text else "(页眉文本)"}</div>'
    else:
        header_preview = '<div style="color:#999;font-size:12px;text-align:center;">页眉未启用</div>'

    footer_preview = ""
    if footer_enabled:
        pn_sample = "1" if footer_pn_fmt == "arabic" else "I" if footer_pn_fmt == "roman" else "一" if footer_pn_fmt == "chinese" else ""
        footer_preview = f'<div style="font-size:{footer_size}pt;font-family:{footer_font};text-align:{footer_align};">{pn_sample}</div>'
    else:
        footer_preview = '<div style="color:#999;font-size:12px;text-align:center;">页脚未启用</div>'

    # Pagination: estimate lines per page (1pt ≈ 1.333px, A4=210x297mm)
    margin_top_mm = page_cfg.get("margin_top", 2.54) * 10
    margin_bottom_mm = page_cfg.get("margin_bottom", 2.54) * 10
    margin_left_mm = page_cfg.get("margin_left", 3.18) * 10
    margin_right_mm = page_cfg.get("margin_right", 2.54) * 10
    usable_height_px = int((297 - margin_top_mm - margin_bottom_mm) * 3.78)
    usable_width_px = int((210 - margin_left_mm - margin_right_mm) * 3.78)
    # Average char width: Chinese char ≈ body_size * 1.333px, estimate 0.6em per char
    char_width_px = body_size * 1.333 * 0.55
    chars_per_line = max(int(usable_width_px / char_width_px), 30)
    para_line_px = body_size * 1.333 * line_spacing + (6 if paragraph_spacing else 4)
    lines_per_page = max(int(usable_height_px / para_line_px), 15)

    body_paras = state.get_body_sample()
    body_items = ""
    pages = [[]]
    page_heights = [0]

    def _para_html(pi, text, style):
        if "Heading 1" in style:
            return f'<div class="body-h1 annotatable" data-section="body" data-idx="{pi}" onclick="onAnnotatableClick(this)"><span class="note-badge"></span>{text}</div>'
        elif "Heading 2" in style:
            return f'<div class="body-h2 annotatable" data-section="body" data-idx="{pi}" onclick="onAnnotatableClick(this)"><span class="note-badge"></span>{text}</div>'
        elif "Heading 3" in style:
            return f'<div class="body-h3 annotatable" data-section="body" data-idx="{pi}" onclick="onAnnotatableClick(this)"><span class="note-badge"></span>{text}</div>'
        return f'<div class="body-para annotatable" data-section="body" data-idx="{pi}" onclick="onAnnotatableClick(this)"><span class="note-badge"></span>{text}</div>'

    def _estimate_height(text, style):
        if "Heading 1" in style:
            return h1.get("size", 16) * 1.333 + 24  # margin 16+8
        elif "Heading 2" in style:
            return h2.get("size", 14) * 1.333 + 18  # margin 12+6
        elif "Heading 3" in style:
            return h3.get("size", 13) * 1.333 + 14  # margin 10+4
        n_lines = max(1, (len(text) + chars_per_line - 1) // chars_per_line)
        return n_lines * para_line_px + (6 if paragraph_spacing else 4)

    for i, p in enumerate(body_paras):
        text = p.get("text", "").strip()
        style = p.get("style", "") or ""
        if not text:
            continue
        snippet = text[:120] + ("..." if len(text) > 120 else "")
        body_items += _para_html(i, snippet, style)
        est_h = _estimate_height(text, style)
        if page_heights[-1] + est_h > usable_height_px and page_heights[-1] > 0:
            pages.append([])
            page_heights.append(0)
        pages[-1].append(_para_html(i, text, style))
        page_heights[-1] += est_h

    header_text_display = header_text if header_enabled else ""
    pn_fmt_func = lambda n: str(n) if footer_pn_fmt == "arabic" else {1:"I",2:"II",3:"III",4:"IV",5:"V"}.get(n, str(n)) if footer_pn_fmt == "roman" else {1:"一",2:"二",3:"三",4:"四",5:"五"}.get(n, str(n)) if footer_pn_fmt == "chinese" else str(n)
    body_pages_html = ""
    for pg_idx, pg_paras in enumerate(pages):
        pn = pg_idx + 1
        pg_content = "".join(pg_paras)
        pn_display = pn_fmt_func(pn)
        body_pages_html += f'''
        <div class="word-page">
            <div class="word-page-header">{header_text_display}</div>
            <div class="word-page-body">{pg_content}</div>
            <div class="word-page-footer"><span class="word-page-number">{pn_display}</span></div>
        </div>'''

    html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<title>文档设计预览 - DOCX Master</title>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ font-family: "{chinese_font}", sans-serif; background: #f0f2f5; color: #333; }}
.header {{ background: linear-gradient(135deg, #1a73e8, #4285f4); color: white; padding: 20px 40px; position: relative; }}
.header h1 {{ font-size: 22px; font-weight: 600; }}
.header p {{ font-size: 13px; opacity: 0.85; margin-top: 4px; }}
.language-switcher {{ position: absolute; top: 20px; right: 20px; display: flex; align-items: center; gap: 8px; background: rgba(255,255,255,0.2); padding: 8px 12px; border-radius: 20px; cursor: pointer; transition: all 0.2s; }}
.language-switcher:hover {{ background: rgba(255,255,255,0.3); }}
.language-switcher svg {{ width: 18px; height: 18px; }}
.language-switcher select {{ background: transparent; border: none; color: white; font-size: 14px; cursor: pointer; outline: none; }}
.language-switcher select option {{ background: #333; color: white; }}
.container {{ max-width: 1200px; margin: 20px auto; padding: 0 20px; display: grid; grid-template-columns: 1fr 380px; gap: 20px; }}
.main {{ display: flex; flex-direction: column; gap: 16px; }}
.sidebar {{ display: flex; flex-direction: column; gap: 16px; }}
.section-block {{ background: white; border-radius: 8px; padding: 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
.section-title {{ font-size: 16px; font-weight: 600; margin-bottom: 12px; color: #1a73e8; }}
.badge {{ font-size: 11px; background: #e8f5e9; color: #2e7d32; padding: 2px 8px; border-radius: 10px; font-weight: 400; }}
.badge.empty {{ background: #fff3e0; color: #e65100; }}
.badge.gen {{ background: #e3f2fd; color: #1565c0; }}
.info-text {{ color: #888; font-size: 13px; }}
.cover-preview {{ border: 2px dashed #ccc; border-radius: 6px; padding: 30px 20px; text-align: center; background: #fafafa; min-height: 160px; display: flex; flex-direction: column; justify-content: center; gap: 8px; }}
.cover-item {{ font-size: 16px; color: #333; }}
.cover-item.empty {{ height: 20px; }}
.toc-preview {{ border: 1px solid #e0e0e0; border-radius: 6px; padding: 16px; background: #fafafa; max-height: 200px; overflow-y: auto; }}
.toc-item {{ padding: 3px 0; font-size: 13px; border-bottom: 1px dotted #eee; }}
.page-preview {{ border: 1px solid #e0e0e0; border-radius: 6px; padding: 16px 24px; background: #fff; position: relative; min-height: 100px; }}
.page-header-area {{ border-bottom: {"1px solid #333" if header_sep else "none"}; padding-bottom: 6px; margin-bottom: 12px; min-height: 20px; }}
.page-body-area {{ min-height: 40px; color: #bbb; font-size: 12px; text-align: center; padding: 10px 0; }}
.page-footer-area {{ border-top: 1px solid #e0e0e0; padding-top: 6px; margin-top: 12px; min-height: 20px; }}
.body-h1 {{ font-family: "{heading_font}", sans-serif; font-size: {h1.get("size", 16)}pt; font-weight: {"bold" if h1.get("bold", True) else "normal"}; text-align: {"center" if h1.get("alignment", "center") == "center" else "left"}; color: {h1.get("color", "#000000")}; margin: 16px 0 8px; padding-bottom: 6px; border-bottom: 1px solid #eee; }}
.body-h2 {{ font-family: "{heading_font}", sans-serif; font-size: {h2.get("size", 14)}pt; font-weight: {"bold" if h2.get("bold", True) else "normal"}; text-align: left; color: {h2.get("color", "#000000")}; margin: 12px 0 6px; }}
.body-h3 {{ font-family: "{heading_font}", sans-serif; font-size: {h3.get("size", 13)}pt; font-weight: {"bold" if h3.get("bold", True) else "normal"}; text-align: left; color: {h3.get("color", "#000000")}; margin: 10px 0 4px; }}
.body-para {{ font-family: "{chinese_font}", serif; font-size: {body_size}pt; line-height: {line_spacing}; text-indent: {first_indent}em; margin: {"6px 0" if paragraph_spacing else "4px 0"}; text-align: justify; }}
.control-row {{ margin-top: 12px; padding-top: 10px; border-top: 1px solid #f0f0f0; }}
.control-row label {{ font-size: 13px; cursor: pointer; display: flex; align-items: center; gap: 6px; }}
.control-row input[type="checkbox"] {{ width: 16px; height: 16px; accent-color: #1a73e8; }}
.config-group {{ margin-bottom: 14px; }}
.config-group h3 {{ font-size: 13px; font-weight: 600; color: #555; margin-bottom: 8px; }}
.config-row {{ display: flex; align-items: center; gap: 8px; margin-bottom: 6px; }}
.config-row label {{ font-size: 12px; color: #666; min-width: 70px; }}
.config-row input, .config-row select {{ flex: 1; padding: 4px 8px; border: 1px solid #ddd; border-radius: 4px; font-size: 12px; }}
.config-row input[type="number"] {{ width: 60px; flex: none; }}
.config-row input[type="color"] {{ width: 40px; height: 28px; padding: 2px; flex: none; }}
.toggle-group {{ background: #f8f9fa; border-radius: 6px; padding: 12px; margin-bottom: 12px; }}
.toggle-header {{ display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px; }}
.toggle-header label {{ font-size: 13px; font-weight: 600; color: #333; cursor: pointer; display: flex; align-items: center; gap: 6px; }}
.toggle-body {{ display: none; }}
.toggle-body.show {{ display: block; }}
.btn {{ padding: 10px 24px; border: none; border-radius: 6px; font-size: 14px; cursor: pointer; font-weight: 600; }}
.btn-primary {{ background: #1a73e8; color: white; }}
.btn-primary:hover {{ background: #1557b0; }}
.btn-secondary {{ background: #f0f0f0; color: #333; }}
.btn-secondary:hover {{ background: #e0e0e0; }}
.btn-row {{ display: flex; gap: 10px; margin-top: 16px; position: sticky; bottom: 0; background: white; padding: 12px 0; border-top: 1px solid #eee; }}

/* ===== Word-like Page View ===== */
.pages-container {{ display: flex; flex-direction: column; align-items: center; gap: 24px; padding: 10px 0; }}
.word-page {{ width: 100%; background: white; border: 1px solid #d0d0d0; border-radius: 2px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); position: relative; overflow: hidden; }}
.word-page-header {{ padding: {max(int(page_cfg.get("margin_top", 2.54) * 3.78) - 8, 8)}px {max(int(page_cfg.get("margin_right", 2.54) * 3.78), 16)}px 8px {max(int(page_cfg.get("margin_left", 3.18) * 3.78), 16)}px; border-bottom: {"1px solid #333" if header_sep else "1px solid #e0e0e0"}; font-size: {header_size}pt; font-family: "{header_font}"; text-align: {header_align}; color: {"#333" if header_enabled else "transparent"}; min-height: 18px; }}
.word-page-footer {{ padding: 8px {max(int(page_cfg.get("margin_right", 2.54) * 3.78), 16)}px {max(int(page_cfg.get("margin_bottom", 2.54) * 3.78) - 8, 8)}px {max(int(page_cfg.get("margin_left", 3.18) * 3.78), 16)}px; border-top: 1px solid #e0e0e0; display: flex; justify-content: space-between; align-items: center; min-height: 20px; }}
.word-page-number {{ font-size: 9pt; font-family: "{footer_font}"; text-align: {footer_align}; color: #666; }}
.word-page-body {{ padding: 4px {max(int(page_cfg.get("margin_right", 2.54) * 3.78), 16)}px 4px {max(int(page_cfg.get("margin_left", 3.18) * 3.78), 16)}px; }}
.view-toggle {{ display: flex; gap: 6px; }}
.view-toggle button {{ padding: 4px 12px; border: 1px solid #ddd; background: white; color: #666; border-radius: 4px; cursor: pointer; font-size: 12px; transition: all 0.2s; }}
.view-toggle button.active {{ background: #1a73e8; color: white; border-color: #1a73e8; }}
.view-toggle button:hover:not(.active) {{ background: #f0f0f0; }}

/* ===== Note Annotation Styles ===== */
.annotatable {{ position: relative; cursor: pointer; transition: all 0.2s; border-left: 3px solid transparent; padding-left: 8px; }}
.annotatable:hover {{ background: rgba(26, 115, 232, 0.06); border-left-color: #1a73e8; border-radius: 0 4px 4px 0; }}
.annotatable.has-note {{ border-left-color: #ff9800; background: rgba(255, 152, 0, 0.06); }}
.annotatable.has-note:hover {{ border-left-color: #f57c00; background: rgba(255, 152, 0, 0.1); }}
.note-badge {{ position: absolute; top: -6px; right: -6px; background: #ff9800; color: white; font-size: 10px; width: 18px; height: 18px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; box-shadow: 0 1px 3px rgba(0,0,0,0.2); display: none; }}
.annotatable.has-note .note-badge {{ display: flex; }}

.note-fab {{ position: fixed; bottom: 24px; right: 24px; width: 56px; height: 56px; border-radius: 50%; background: #1a73e8; color: white; border: none; cursor: pointer; font-size: 22px; box-shadow: 0 4px 12px rgba(26,115,232,0.4); transition: all 0.3s; z-index: 900; display: flex; align-items: center; justify-content: center; }}
.note-fab:hover {{ transform: scale(1.1); box-shadow: 0 6px 16px rgba(26,115,232,0.5); background: #1557b0; }}
.note-fab .fab-count {{ position: absolute; top: -4px; right: -4px; background: #e53935; color: white; font-size: 11px; width: 20px; height: 20px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; }}

.note-panel {{ position: fixed; top: 0; right: -420px; width: 400px; height: 100vh; background: white; box-shadow: -4px 0 20px rgba(0,0,0,0.15); z-index: 1000; transition: right 0.3s ease; display: flex; flex-direction: column; }}
.note-panel.open {{ right: 0; }}
.note-panel-header {{ background: linear-gradient(135deg, #1a73e8, #4285f4); color: white; padding: 16px 20px; display: flex; align-items: center; justify-content: space-between; flex-shrink: 0; }}
.note-panel-header h3 {{ font-size: 16px; font-weight: 600; }}
.note-panel-close {{ background: rgba(255,255,255,0.2); border: none; color: white; width: 32px; height: 32px; border-radius: 50%; cursor: pointer; font-size: 18px; display: flex; align-items: center; justify-content: center; }}
.note-panel-close:hover {{ background: rgba(255,255,255,0.3); }}
.note-panel-body {{ flex: 1; overflow-y: auto; padding: 16px; }}
.note-panel-footer {{ padding: 12px 16px; border-top: 1px solid #eee; display: flex; gap: 8px; flex-shrink: 0; }}
.note-empty {{ text-align: center; color: #999; padding: 40px 20px; font-size: 14px; }}
.note-empty svg {{ width: 48px; height: 48px; margin-bottom: 12px; opacity: 0.3; }}
.note-card {{ background: #f8f9fa; border-radius: 8px; padding: 12px; margin-bottom: 10px; border-left: 3px solid #ff9800; position: relative; }}
.note-card-header {{ display: flex; align-items: center; justify-content: space-between; margin-bottom: 6px; }}
.note-card-source {{ font-size: 11px; color: #888; background: #e8f0fe; padding: 2px 8px; border-radius: 10px; }}
.note-card-text {{ font-size: 13px; color: #333; line-height: 1.5; word-break: break-word; }}
.note-card-delete {{ position: absolute; top: 8px; right: 8px; background: none; border: none; color: #ccc; cursor: pointer; font-size: 16px; padding: 2px 6px; border-radius: 4px; }}
.note-card-delete:hover {{ color: #e53935; background: #ffebee; }}

.note-modal-overlay {{ position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.4); z-index: 1100; display: none; align-items: center; justify-content: center; }}
.note-modal-overlay.show {{ display: flex; }}
.note-modal {{ background: white; border-radius: 12px; padding: 24px; width: 420px; max-width: 90vw; box-shadow: 0 20px 60px rgba(0,0,0,0.3); }}
.note-modal h3 {{ font-size: 16px; font-weight: 600; color: #333; margin-bottom: 8px; }}
.note-modal .note-source-preview {{ font-size: 12px; color: #888; background: #f0f0f0; padding: 8px 12px; border-radius: 6px; margin-bottom: 12px; max-height: 60px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }}
.note-modal textarea {{ width: 100%; min-height: 100px; border: 1px solid #ddd; border-radius: 8px; padding: 10px; font-size: 14px; font-family: inherit; resize: vertical; outline: none; }}
.note-modal textarea:focus {{ border-color: #1a73e8; box-shadow: 0 0 0 2px rgba(26,115,232,0.2); }}
.note-modal-actions {{ display: flex; gap: 8px; margin-top: 12px; justify-content: flex-end; }}
.note-overlay {{ position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.3); z-index: 990; display: none; }}
.note-overlay.show {{ display: block; }}
</style>
</head>
<body>
<div class="header">
    <h1>DOCX Master - 文档设计预览</h1>
    <p>请确认封面页、目录页、页眉页脚和正文样式，修改后点击"确认并继续"</p>
    <div class="language-switcher">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="10"></circle>
            <line x1="2" y1="12" x2="22" y2="12"></line>
            <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"></path>
        </svg>
        <select id="languageSelect" onchange="changeLanguage(this.value)">
            <option value="zh">中文</option>
            <option value="en">English</option>
        </select>
    </div>
</div>
<div class="container">
<div class="main">
    {cover_section}
    {toc_existing_section}
    <div class="section-block">
        <h2 class="section-title">页眉页脚预览</h2>
        <div class="page-preview">
            <div class="page-header-area">{header_preview}</div>
            <div class="page-body-area">（正文内容区域）</div>
            <div class="page-footer-area">{footer_preview}</div>
        </div>
    </div>
    <div class="section-block">
        <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:12px;">
            <h2 class="section-title" style="margin-bottom:0;">正文样式预览</h2>
            <div class="view-toggle">
                <button class="active" onclick="switchView('list',this)" title="列表视图">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="8" y1="6" x2="21" y2="6"/><line x1="8" y1="12" x2="21" y2="12"/><line x1="8" y1="18" x2="21" y2="18"/><line x1="3" y1="6" x2="3.01" y2="6"/><line x1="3" y1="12" x2="3.01" y2="12"/><line x1="3" y1="18" x2="3.01" y2="18"/></svg>
                </button>
                <button onclick="switchView('page',this)" title="分页视图">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14,2 14,8 21,8"/></svg>
                </button>
            </div>
        </div>
        <div id="body-view-list" style="border: 1px solid #e0e0e0; border-radius: 6px; padding: 16px; background: #fff;">
            {body_items}
        </div>
        <div id="body-view-page" class="pages-container" style="display:none;">
            {body_pages_html}
        </div>
    </div>
</div>
<div class="sidebar">
    <div class="section-block">
        <h2 class="section-title">样式配置</h2>

        <div class="toggle-group" id="cover-design-group" style="display: {'block' if cover_enabled else 'none'};">
            <div class="toggle-header">
                <label>封面设计</label>
                <span class="badge gen">自定义</span>
            </div>
            <div class="toggle-body show" id="cover-design-options">
                <div class="config-group">
                    <h3>大标题</h3>
                    <div class="config-row"><label>标题文本</label><input type="text" id="cfg-cover-title-text" value="{cover_title.get('text', '课程作业')}"></div>
                    <div class="config-row"><label>字体</label><input type="text" id="cfg-cover-title-font" value="{cover_title.get('font', '黑体')}"></div>
                    <div class="config-row"><label>字号</label><input type="number" id="cfg-cover-title-size" value="{cover_title.get('size', 22)}" min="16" max="36"></div>
                    <div class="config-row"><label>对齐</label>
                        <select id="cfg-cover-title-align">
                            <option value="center" {"selected" if cover_title.get('alignment') == 'center' else ""}>居中</option>
                            <option value="left" {"selected" if cover_title.get('alignment') == 'left' else ""}>左对齐</option>
                        </select>
                    </div>
                    <div class="config-row"><label>颜色</label><input type="color" id="cfg-cover-title-color" value="{cover_title.get('color', '#000000')}"></div>
                </div>

                <div class="config-group">
                    <h3>学校信息</h3>
                    <div class="config-row"><label>学校名称</label><input type="text" id="cfg-cover-school-name" value="{cover_cfg.get('school_name', '')}" placeholder="如：XX大学"></div>
                    <div class="config-row"><label>字体</label><input type="text" id="cfg-cover-school-font" value="{cover_cfg.get('school_font', '宋体')}"></div>
                    <div class="config-row"><label>字号</label><input type="number" id="cfg-cover-school-size" value="{cover_cfg.get('school_size', 18)}" min="14" max="28"></div>
                </div>

                <div class="config-group">
                    <h3>个人信息</h3>
                    <div id="cover-info-items">
                        {"".join(f'<div class="config-row cover-info-row"><label>{item.get("label", "")}</label><input type="text" class="cover-info-value" data-label="{item.get("label", "")}" value="{item.get("value", "")}" placeholder="请输入{item.get("label", "")}"></div>' for item in cover_info_items)}
                    </div>
                    <button class="btn btn-secondary" style="margin-top:8px;font-size:12px;padding:4px 12px;" onclick="addCoverInfoItem()">+ 添加信息项</button>
                </div>

                <div class="config-group">
                    <h3>学校标志</h3>
                    <div class="config-row"><label><input type="checkbox" id="cfg-cover-logo-enabled" {"checked" if cover_logo.get('enabled') else ""}> 显示Logo</label></div>
                    <div class="config-row"><label>Logo图片</label><input type="file" id="cfg-cover-logo-file" accept="image/*" onchange="handleLogoUpload(this)"></div>
                    <div class="config-row"><label>宽度(px)</label><input type="number" id="cfg-cover-logo-width" value="{cover_logo.get('width', 120)}" min="50" max="300"></div>
                    <div class="config-row"><label>高度(px)</label><input type="number" id="cfg-cover-logo-height" value="{cover_logo.get('height', 120)}" min="50" max="300"></div>
                    <div class="config-row"><label>位置</label>
                        <select id="cfg-cover-logo-position">
                            <option value="top" {"selected" if cover_logo.get('position') == 'top' else ""}>顶部</option>
                            <option value="center" {"selected" if cover_logo.get('position') == 'center' else ""}>居中</option>
                        </select>
                    </div>
                </div>

                <div class="config-group">
                    <h3>布局设置</h3>
                    <div class="config-row"><label>垂直对齐</label>
                        <select id="cfg-cover-layout-valign">
                            <option value="center" {"selected" if cover_layout.get('vertical_align') == 'center' else ""}>居中</option>
                            <option value="top" {"selected" if cover_layout.get('vertical_align') == 'top' else ""}>顶部</option>
                        </select>
                    </div>
                    <div class="config-row"><label>标题后间距</label><input type="number" id="cfg-cover-layout-spacing-title" value="{cover_layout.get('spacing_after_title', 60)}" min="20" max="120"></div>
                    <div class="config-row"><label>信息项间距</label><input type="number" id="cfg-cover-layout-spacing-items" value="{cover_layout.get('spacing_between_items', 10)}" min="5" max="30"></div>
                </div>
            </div>
        </div>

        <div class="config-group">
            <h3>正文字体</h3>
            <div class="config-row"><label>中文字体</label><input type="text" id="cfg-chinese-font" value="{chinese_font}"></div>
            <div class="config-row"><label>英文字体</label><input type="text" id="cfg-english-font" value="{english_font}"></div>
            <div class="config-row"><label>字号</label><input type="number" id="cfg-body-size" value="{body_size}" min="10" max="18"></div>
            <div class="config-row"><label>行距</label><input type="number" id="cfg-line-spacing" value="{line_spacing}" min="1" max="3" step="0.1"></div>
            <div class="config-row"><label>首行缩进</label><input type="number" id="cfg-first-indent" value="{first_indent}" min="0" max="4" step="0.5"></div>
            <div class="config-row"><label><input type="checkbox" id="cfg-para-spacing" {"checked" if paragraph_spacing else ""}> 段落之间空行分隔</label></div>
        </div>

        <div class="config-group">
            <h3>标题样式</h3>
            <div class="config-row"><label>标题字体</label><input type="text" id="cfg-heading-font" value="{heading_font}"></div>
            <div class="config-row"><label>H1 字号</label><input type="number" id="cfg-h1-size" value="{h1.get("size", 16)}" min="12" max="24"></div>
            <div class="config-row"><label>H1 对齐</label>
                <select id="cfg-h1-align">
                    <option value="center" {"selected" if h1.get("alignment") == "center" else ""}>居中</option>
                    <option value="left" {"selected" if h1.get("alignment") == "left" else ""}>左对齐</option>
                </select>
            </div>
            <div class="config-row"><label>H1 颜色</label><input type="color" id="cfg-h1-color" value="{h1.get("color", "#000000")}"></div>
        </div>

        <div class="toggle-group">
            <div class="toggle-header">
                <label><input type="checkbox" id="cfg-toc-enabled" {"checked" if toc_enabled else ""} onchange="toggleSection('toc')"> 自动生成目录页</label>
                <span class="badge gen">生成</span>
            </div>
            <div class="toggle-body {"show" if toc_enabled else ""}" id="toc-options">
                <div class="config-row"><label>目录标题</label><input type="text" id="cfg-toc-title" value="{toc_title}"></div>
                <div class="config-row"><label>标题字体</label><input type="text" id="cfg-toc-title-font" value="{toc_title_font}"></div>
                <div class="config-row"><label>标题字号</label><input type="number" id="cfg-toc-title-size" value="{toc_title_size}" min="12" max="24"></div>
                <div class="config-row"><label>条目字体</label><input type="text" id="cfg-toc-entry-font" value="{toc_entry_font}"></div>
                <div class="config-row"><label>条目字号</label><input type="number" id="cfg-toc-entry-size" value="{toc_entry_size}" min="9" max="16"></div>
                <div class="config-row"><label>最大级别</label>
                    <select id="cfg-toc-max-level">
                        <option value="1" {"selected" if toc_max_level == 1 else ""}>仅 H1</option>
                        <option value="2" {"selected" if toc_max_level == 2 else ""}>H1-H2</option>
                        <option value="3" {"selected" if toc_max_level == 3 else ""}>H1-H3</option>
                    </select>
                </div>
                <div class="config-row"><label>缩进量(em)</label><input type="number" id="cfg-toc-indent" value="{toc_indent_step}" min="0" max="6" step="0.5"></div>
                <div class="config-row"><label><input type="checkbox" id="cfg-toc-dots" {"checked" if toc_dot_leaders else ""}> 显示前导点</label></div>
                <div style="margin-top:8px;">
                    <div style="font-size:11px;color:#888;margin-bottom:4px;">目录预览（基于文档标题，仅供参考）：</div>
                    <div class="toc-preview" style="max-height:150px;">{toc_heading_preview}</div>
                    <div style="font-size:11px;color:#1a73e8;margin-top:6px;">实际目录将由 Word TOC 域自动生成，包含页码、层级缩进和前导点。在 Word 中按 Ctrl+A 后按 F9 更新域。</div>
                </div>
            </div>
        </div>

        <div class="toggle-group">
            <div class="toggle-header">
                <label><input type="checkbox" id="cfg-header-enabled" {"checked" if header_enabled else ""} onchange="toggleSection('header')"> 设置页眉</label>
            </div>
            <div class="toggle-body {"show" if header_enabled else ""}" id="header-options">
                <div class="config-row"><label>页眉文本</label><input type="text" id="cfg-header-text" value="{header_text}" placeholder="如：XX大学学报"></div>
                <div class="config-row"><label>字体</label><input type="text" id="cfg-header-font" value="{header_font}"></div>
                <div class="config-row"><label>字号</label><input type="number" id="cfg-header-size" value="{header_size}" min="6" max="14"></div>
                <div class="config-row"><label>对齐</label>
                    <select id="cfg-header-align">
                        <option value="left" {"selected" if header_align == "left" else ""}>左对齐</option>
                        <option value="center" {"selected" if header_align == "center" else ""}>居中</option>
                        <option value="right" {"selected" if header_align == "right" else ""}>右对齐</option>
                    </select>
                </div>
                <div class="config-row"><label><input type="checkbox" id="cfg-header-sep" {"checked" if header_sep else ""}> 显示分隔线</label></div>
            </div>
        </div>

        <div class="toggle-group">
            <div class="toggle-header">
                <label><input type="checkbox" id="cfg-footer-enabled" {"checked" if footer_enabled else ""} onchange="toggleSection('footer')"> 设置页脚页码</label>
            </div>
            <div class="toggle-body {"show" if footer_enabled else ""}" id="footer-options">
                <div class="config-row"><label>页码格式</label>
                    <select id="cfg-footer-pn-fmt">
                        <option value="arabic" {"selected" if footer_pn_fmt == "arabic" else ""}>阿拉伯数字 (1, 2, 3)</option>
                        <option value="roman" {"selected" if footer_pn_fmt == "roman" else ""}>罗马数字 (I, II, III)</option>
                        <option value="chinese" {"selected" if footer_pn_fmt == "chinese" else ""}>中文数字 (一, 二, 三)</option>
                    </select>
                </div>
                <div class="config-row"><label>字体</label><input type="text" id="cfg-footer-font" value="{footer_font}"></div>
                <div class="config-row"><label>字号</label><input type="number" id="cfg-footer-size" value="{footer_size}" min="6" max="14"></div>
                <div class="config-row"><label>对齐</label>
                    <select id="cfg-footer-align">
                        <option value="left" {"selected" if footer_align == "left" else ""}>左对齐</option>
                        <option value="center" {"selected" if footer_align == "center" else ""}>居中</option>
                        <option value="right" {"selected" if footer_align == "right" else ""}>右对齐</option>
                    </select>
                </div>
            </div>
        </div>

        <div class="config-group">
            <h3>页面设置</h3>
            <div class="config-row"><label>上边距(cm)</label><input type="number" id="cfg-margin-top" value="{page_cfg.get("margin_top", 2.54)}" min="1" max="5" step="0.1"></div>
            <div class="config-row"><label>左边距(cm)</label><input type="number" id="cfg-margin-left" value="{page_cfg.get("margin_left", 3.18)}" min="1" max="5" step="0.1"></div>
        </div>

        <div class="btn-row">
            <button class="btn btn-primary" onclick="confirmDesign()">确认并继续</button>
            <button class="btn btn-secondary" onclick="resetDefaults()">重置默认</button>
        </div>
    </div>
</div>
</div>
<script>
// Language translations
const translations = {{
    zh: {{
        title: '文档设计预览 - DOCX Master',
        headerTitle: 'DOCX Master - 文档设计预览',
        headerDesc: '请确认封面页、目录页、页眉页脚和正文样式，修改后点击"确认并继续"',
        coverSection: '封面页',
        coverDetected: '已检测到',
        coverNotDetected: '未检测到',
        keepCover: '保留原始封面页设计',
        redesignCover: '重新设计封面页',
        designCover: '设计封面页',
        tocSection: '已有目录页',
        tocDetected: '已检测到',
        tocNotDetected: '未检测到',
        keepToc: '保留原始目录页设计',
        autoGenerateToc: '自动生成目录页',
        headerFooterPreview: '页眉页脚预览',
        bodyPreview: '正文样式预览',
        styleConfig: '样式配置',
        coverDesign: '封面设计',
        custom: '自定义',
        mainTitle: '大标题',
        titleText: '标题文本',
        font: '字体',
        fontSize: '字号',
        alignment: '对齐',
        center: '居中',
        left: '左对齐',
        color: '颜色',
        schoolInfo: '学校信息',
        schoolName: '学校名称',
        personalInfo: '个人信息',
        addInfoItem: '+ 添加信息项',
        schoolLogo: '学校标志',
        showLogo: '显示Logo',
        logoImage: 'Logo图片',
        width: '宽度(px)',
        height: '高度(px)',
        position: '位置',
        top: '顶部',
        layoutSettings: '布局设置',
        verticalAlign: '垂直对齐',
        spacingAfterTitle: '标题后间距',
        spacingBetweenItems: '信息项间距',
        bodyFont: '正文字体',
        chineseFont: '中文字体',
        englishFont: '英文字体',
        bodySize: '字号',
        lineSpacing: '行距',
        firstIndent: '首行缩进',
        paraSpacing: '段落之间空行分隔',
        headingStyle: '标题样式',
        headingFont: '标题字体',
        h1Size: 'H1 字号',
        h1Align: 'H1 对齐',
        h1Color: 'H1 颜色',
        tocTitle: '目录标题',
        tocTitleFont: '标题字体',
        tocTitleSize: '标题字号',
        tocEntryFont: '条目字体',
        tocEntrySize: '条目字号',
        tocMaxLevel: '最大级别',
        onlyH1: '仅 H1',
        h1ToH2: 'H1-H2',
        h1ToH3: 'H1-H3',
        tocIndent: '缩进量(em)',
        showDotLeaders: '显示前导点',
        tocPreview: '目录预览（基于文档标题，仅供参考）：',
        tocNote: '实际目录将由 Word TOC 域自动生成，包含页码、层级缩进和前导点。在 Word 中按 Ctrl+A 后按 F9 更新域。',
        setHeader: '设置页眉',
        headerText: '页眉文本',
        showSeparator: '显示分隔线',
        setFooter: '设置页脚页码',
        pageNumberFormat: '页码格式',
        arabic: '阿拉伯数字 (1, 2, 3)',
        roman: '罗马数字 (I, II, III)',
        chinese: '中文数字 (一, 二, 三)',
        pageSettings: '页面设置',
        marginTop: '上边距(cm)',
        marginLeft: '左边距(cm)',
        confirmAndContinue: '确认并继续',
        resetDefaults: '重置默认',
        designConfirmed: '✓ 设计已确认，处理将继续...',
        newLabel: '新标签',
        enterContent: '请输入内容',
        bodyArea: '（正文内容区域）',
        headerNotEnabled: '页眉未启用',
        footerNotEnabled: '页脚未启用',
        noHeadingsDetected: '未检测到标题，无法自动生成目录',
        noCoverDetected: '文档未检测到封面页。',
        noTocDetected: '文档未检测到目录页。您可以在下方选择自动生成。'
    }},
    en: {{
        title: 'Document Design Preview - DOCX Master',
        headerTitle: 'DOCX Master - Document Design Preview',
        headerDesc: 'Please confirm cover page, TOC, headers/footers and body styles, then click "Confirm and Continue"',
        coverSection: 'Cover Page',
        coverDetected: 'Detected',
        coverNotDetected: 'Not Detected',
        keepCover: 'Keep original cover page design',
        redesignCover: 'Redesign cover page',
        designCover: 'Design cover page',
        tocSection: 'Existing TOC',
        tocDetected: 'Detected',
        tocNotDetected: 'Not Detected',
        keepToc: 'Keep original TOC design',
        autoGenerateToc: 'Auto-generate TOC',
        headerFooterPreview: 'Header & Footer Preview',
        bodyPreview: 'Body Style Preview',
        styleConfig: 'Style Configuration',
        coverDesign: 'Cover Design',
        custom: 'Custom',
        mainTitle: 'Main Title',
        titleText: 'Title Text',
        font: 'Font',
        fontSize: 'Font Size',
        alignment: 'Alignment',
        center: 'Center',
        left: 'Left',
        color: 'Color',
        schoolInfo: 'School Info',
        schoolName: 'School Name',
        personalInfo: 'Personal Info',
        addInfoItem: '+ Add Info Item',
        schoolLogo: 'School Logo',
        showLogo: 'Show Logo',
        logoImage: 'Logo Image',
        width: 'Width(px)',
        height: 'Height(px)',
        position: 'Position',
        top: 'Top',
        layoutSettings: 'Layout Settings',
        verticalAlign: 'Vertical Align',
        spacingAfterTitle: 'Spacing After Title',
        spacingBetweenItems: 'Spacing Between Items',
        bodyFont: 'Body Font',
        chineseFont: 'Chinese Font',
        englishFont: 'English Font',
        bodySize: 'Font Size',
        lineSpacing: 'Line Spacing',
        firstIndent: 'First Indent',
        paraSpacing: 'Paragraph spacing with blank line',
        headingStyle: 'Heading Style',
        headingFont: 'Heading Font',
        h1Size: 'H1 Size',
        h1Align: 'H1 Align',
        h1Color: 'H1 Color',
        tocTitle: 'TOC Title',
        tocTitleFont: 'Title Font',
        tocTitleSize: 'Title Size',
        tocEntryFont: 'Entry Font',
        tocEntrySize: 'Entry Size',
        tocMaxLevel: 'Max Level',
        onlyH1: 'H1 Only',
        h1ToH2: 'H1-H2',
        h1ToH3: 'H1-H3',
        tocIndent: 'Indent(em)',
        showDotLeaders: 'Show dot leaders',
        tocPreview: 'TOC preview (based on document headings, for reference only):',
        tocNote: 'Actual TOC will be auto-generated by Word TOC field, including page numbers, level indentation and leader dots. Press Ctrl+A then F9 in Word to update fields.',
        setHeader: 'Set Header',
        headerText: 'Header Text',
        showSeparator: 'Show separator line',
        setFooter: 'Set Footer Page Number',
        pageNumberFormat: 'Page Number Format',
        arabic: 'Arabic (1, 2, 3)',
        roman: 'Roman (I, II, III)',
        chinese: 'Chinese (一, 二, 三)',
        pageSettings: 'Page Settings',
        marginTop: 'Top Margin(cm)',
        marginLeft: 'Left Margin(cm)',
        confirmAndContinue: 'Confirm and Continue',
        resetDefaults: 'Reset Defaults',
        designConfirmed: '✓ Design confirmed, processing will continue...',
        newLabel: 'New Label',
        enterContent: 'Enter content',
        bodyArea: '(Body content area)',
        headerNotEnabled: 'Header not enabled',
        footerNotEnabled: 'Footer not enabled',
        noHeadingsDetected: 'No headings detected, cannot auto-generate TOC',
        noCoverDetected: 'No cover page detected in document.',
        noTocDetected: 'No TOC detected in document. You can choose to auto-generate below.'
    }}
}};

let currentLang = localStorage.getItem('language') || 'zh';

function t(key) {{
    return translations[currentLang][key] || key;
}}

function changeLanguage(lang) {{
    currentLang = lang;
    localStorage.setItem('language', lang);
    applyTranslations();
}}

function applyTranslations() {{
    document.title = t('title');
    // Update header
    const header = document.querySelector('.header');
    if (header) {{
        header.querySelector('h1').textContent = t('headerTitle');
        header.querySelector('p').textContent = t('headerDesc');
    }}
    // Update language select
    document.getElementById('languageSelect').value = currentLang;
}}

// Initialize language
applyTranslations();

function switchView(mode, btn) {{
    document.getElementById('body-view-list').style.display = mode === 'list' ? 'block' : 'none';
    document.getElementById('body-view-page').style.display = mode === 'page' ? 'flex' : 'none';
    document.querySelectorAll('.view-toggle button').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
}}

function toggleSection(name) {{
    const cb = document.getElementById("cfg-" + name + "-enabled");
    const body = document.getElementById(name + "-options");
    if (cb && body) body.classList.toggle("show", cb.checked);
}}

function toggleCoverDesign() {{
    const cb = document.getElementById("redesign-cover");
    const group = document.getElementById("cover-design-group");
    if (cb && group) group.style.display = cb.checked ? "block" : "none";
}}

function addCoverInfoItem() {{
    const container = document.getElementById("cover-info-items");
    const div = document.createElement("div");
    div.className = "config-row cover-info-row";
    div.innerHTML = '<label><input type="text" class="cover-info-label" value="新标签" style="width:60px;"></label><input type="text" class="cover-info-value" placeholder="请输入内容"><button style="background:none;border:none;color:#e53935;cursor:pointer;font-size:16px;" onclick="this.parentElement.remove()">×</button>';
    container.appendChild(div);
}}

function handleLogoUpload(input) {{
    if (input.files && input.files[0]) {{
        const reader = new FileReader();
        reader.onload = function(e) {{
            window._coverLogoData = e.target.result;
        }};
        reader.readAsDataURL(input.files[0]);
    }}
}}

function getCoverConfig() {{
    const infoItems = [];
    document.querySelectorAll(".cover-info-row").forEach(row => {{
        const labelInput = row.querySelector(".cover-info-label");
        const valueInput = row.querySelector(".cover-info-value");
        const label = labelInput ? labelInput.value : (valueInput ? valueInput.dataset.label : "");
        const value = valueInput ? valueInput.value : "";
        if (label) infoItems.push({{ label: label, value: value, font: "宋体", size: 14 }});
    }});

    return {{
        enabled: document.getElementById("redesign-cover") ? document.getElementById("redesign-cover").checked : false,
        school_name: document.getElementById("cfg-cover-school-name") ? document.getElementById("cfg-cover-school-name").value : "",
        school_font: document.getElementById("cfg-cover-school-font") ? document.getElementById("cfg-cover-school-font").value : "宋体",
        school_size: document.getElementById("cfg-cover-school-size") ? parseInt(document.getElementById("cfg-cover-school-size").value) : 18,
        title: {{
            text: document.getElementById("cfg-cover-title-text") ? document.getElementById("cfg-cover-title-text").value : "课程作业",
            font: document.getElementById("cfg-cover-title-font") ? document.getElementById("cfg-cover-title-font").value : "黑体",
            size: document.getElementById("cfg-cover-title-size") ? parseInt(document.getElementById("cfg-cover-title-size").value) : 22,
            bold: true,
            alignment: document.getElementById("cfg-cover-title-align") ? document.getElementById("cfg-cover-title-align").value : "center",
            color: document.getElementById("cfg-cover-title-color") ? document.getElementById("cfg-cover-title-color").value : "#000000"
        }},
        info_items: infoItems,
        logo: {{
            enabled: document.getElementById("cfg-cover-logo-enabled") ? document.getElementById("cfg-cover-logo-enabled").checked : false,
            image_data: window._coverLogoData || "",
            width: document.getElementById("cfg-cover-logo-width") ? parseInt(document.getElementById("cfg-cover-logo-width").value) : 120,
            height: document.getElementById("cfg-cover-logo-height") ? parseInt(document.getElementById("cfg-cover-logo-height").value) : 120,
            position: document.getElementById("cfg-cover-logo-position") ? document.getElementById("cfg-cover-logo-position").value : "top"
        }},
        layout: {{
            vertical_align: document.getElementById("cfg-cover-layout-valign") ? document.getElementById("cfg-cover-layout-valign").value : "center",
            spacing_after_title: document.getElementById("cfg-cover-layout-spacing-title") ? parseInt(document.getElementById("cfg-cover-layout-spacing-title").value) : 60,
            spacing_between_items: document.getElementById("cfg-cover-layout-spacing-items") ? parseInt(document.getElementById("cfg-cover-layout-spacing-items").value) : 10
        }}
    }};
}}

function confirmDesign() {{
    const config = {{
        cover_preserved: document.getElementById("keep-cover") ? document.getElementById("keep-cover").checked : true,
        redesign_cover: document.getElementById("redesign-cover") ? document.getElementById("redesign-cover").checked : false,
        toc_preserved: document.getElementById("keep-toc") ? document.getElementById("keep-toc").checked : true,
        fonts: {{
            chinese: {{ family: document.getElementById("cfg-chinese-font").value, size: parseInt(document.getElementById("cfg-body-size").value) }},
            english: {{ family: document.getElementById("cfg-english-font").value, size: parseInt(document.getElementById("cfg-body-size").value) }},
            heading: {{ family: document.getElementById("cfg-heading-font").value }}
        }},
        heading: {{
            level1: {{ font: document.getElementById("cfg-heading-font").value, size: parseInt(document.getElementById("cfg-h1-size").value), alignment: document.getElementById("cfg-h1-align").value, color: document.getElementById("cfg-h1-color").value, bold: true }},
            level2: {{ font: document.getElementById("cfg-heading-font").value, size: 14, alignment: "left", color: "#000000", bold: true }},
            level3: {{ font: document.getElementById("cfg-heading-font").value, size: 13, alignment: "left", color: "#000000", bold: true }}
        }},
        paragraph: {{
            line_spacing: parseFloat(document.getElementById("cfg-line-spacing").value),
            first_indent: parseFloat(document.getElementById("cfg-first-indent").value),
            paragraph_spacing: document.getElementById("cfg-para-spacing").checked
        }},
        page: {{
            margin_top: parseFloat(document.getElementById("cfg-margin-top").value),
            margin_left: parseFloat(document.getElementById("cfg-margin-left").value)
        }},
        toc: {{
            enabled: document.getElementById("cfg-toc-enabled").checked,
            title: document.getElementById("cfg-toc-title").value,
            title_font: document.getElementById("cfg-toc-title-font").value,
            title_size: parseInt(document.getElementById("cfg-toc-title-size").value),
            entry_font: document.getElementById("cfg-toc-entry-font").value,
            entry_size: parseInt(document.getElementById("cfg-toc-entry-size").value),
            max_level: parseInt(document.getElementById("cfg-toc-max-level").value),
            indent_step: parseFloat(document.getElementById("cfg-toc-indent").value),
            dot_leaders: document.getElementById("cfg-toc-dots").checked
        }},
        header: {{
            enabled: document.getElementById("cfg-header-enabled").checked,
            text: document.getElementById("cfg-header-text").value,
            font: document.getElementById("cfg-header-font").value,
            size: parseInt(document.getElementById("cfg-header-size").value),
            alignment: document.getElementById("cfg-header-align").value,
            separator_line: document.getElementById("cfg-header-sep").checked
        }},
        footer: {{
            enabled: document.getElementById("cfg-footer-enabled").checked,
            page_number_format: document.getElementById("cfg-footer-pn-fmt").value,
            font: document.getElementById("cfg-footer-font").value,
            size: parseInt(document.getElementById("cfg-footer-size").value),
            alignment: document.getElementById("cfg-footer-align").value
        }},
        cover: getCoverConfig()
    }};
    fetch("/confirm", {{
        method: "POST",
        headers: {{"Content-Type": "application/json"}},
        body: JSON.stringify(config)
    }}).then(r => r.json()).then(d => {{
        document.body.innerHTML = '<div style="display:flex;justify-content:center;align-items:center;height:100vh;font-size:24px;color:#2e7d32;">✓ 设计已确认，处理将继续...</div>';
        setTimeout(() => window.close(), 2000);
    }});
}}

/* ===== Note Annotation System ===== */
let noteState = {{ notes: [], currentTarget: null }};

function onAnnotatableClick(el) {{
    const section = el.dataset.section;
    const idx = parseInt(el.dataset.idx);
    const text = el.textContent.trim().substring(0, 80);
    noteState.currentTarget = {{ section, idx, text, element: el }};
    showNoteModal(section, idx, text);
}}

function showNoteModal(section, idx, text) {{
    const overlay = document.getElementById('note-modal-overlay');
    const source = document.getElementById('note-source-preview');
    const textarea = document.getElementById('note-textarea');
    source.textContent = '[' + section.toUpperCase() + '] ' + text;
    // Pre-fill if editing existing note
    const existing = noteState.notes.find(n => n.section === section && n.idx === idx);
    textarea.value = existing ? existing.note : '';
    overlay.classList.add('show');
    textarea.focus();
}}

function closeNoteModal() {{
    document.getElementById('note-modal-overlay').classList.remove('show');
    noteState.currentTarget = null;
}}

function submitNote() {{
    const textarea = document.getElementById('note-textarea');
    const noteText = textarea.value.trim();
    if (!noteText || !noteState.currentTarget) return;

    const {{ section, idx, text, element }} = noteState.currentTarget;

    // Remove existing note for same target
    noteState.notes = noteState.notes.filter(n => !(n.section === section && n.idx === idx));

    // Add new note
    noteState.notes.push({{ section, idx, source_text: text, note: noteText, created_at: new Date().toISOString() }});

    // Update UI
    element.classList.add('has-note');
    const badge = element.querySelector('.note-badge');
    if (badge) badge.style.display = 'flex';

    // Sync to server
    fetch('/api/add_note', {{
        method: 'POST',
        headers: {{ 'Content-Type': 'application/json' }},
        body: JSON.stringify({{ section, idx, source_text: text, note: noteText }})
    }});

    closeNoteModal();
    renderNotePanel();
    updateFabCount();
}}

function deleteNote(section, idx) {{
    noteState.notes = noteState.notes.filter(n => !(n.section === section && n.idx === idx));

    // Update annotatable element
    const el = document.querySelector(`.annotatable[data-section="${{section}}"][data-idx="${{idx}}"]`);
    if (el) {{
        el.classList.remove('has-note');
        const badge = el.querySelector('.note-badge');
        if (badge) badge.style.display = 'none';
    }}

    // Sync to server
    fetch('/api/delete_note', {{
        method: 'POST',
        headers: {{ 'Content-Type': 'application/json' }},
        body: JSON.stringify({{ section, idx }})
    }});

    renderNotePanel();
    updateFabCount();
}}

function toggleNotePanel() {{
    const panel = document.getElementById('note-panel');
    const overlay = document.getElementById('note-overlay');
    panel.classList.toggle('open');
    overlay.classList.toggle('show');
    if (panel.classList.contains('open')) renderNotePanel();
}}

function closeNotePanel() {{
    document.getElementById('note-panel').classList.remove('open');
    document.getElementById('note-overlay').classList.remove('show');
}}

function renderNotePanel() {{
    const body = document.getElementById('note-panel-body');
    if (noteState.notes.length === 0) {{
        body.innerHTML = '<div class="note-empty"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/></svg><div>暂无标注笔记</div><div style="font-size:12px;margin-top:4px;color:#bbb;">点击预览中的任意元素添加修改建议</div></div>';
        return;
    }}
    body.innerHTML = noteState.notes.map((n, i) => `
        <div class="note-card">
            <div class="note-card-header">
                <span class="note-card-source">${{n.section.toUpperCase()}} #${{n.idx + 1}}</span>
            </div>
            <div class="note-card-text">${{n.source_text}}</div>
            <div style="font-size:12px;color:#555;margin-top:6px;padding-top:6px;border-top:1px dashed #ddd;">${{n.note}}</div>
            <button class="note-card-delete" onclick="deleteNote('${{n.section}}', ${{n.idx}})" title="删除">×</button>
        </div>
    `).join('');
}}

function updateFabCount() {{
    const count = noteState.notes.length;
    const fab = document.getElementById('note-fab-count');
    if (count > 0) {{
        fab.textContent = count;
        fab.style.display = 'flex';
    }} else {{
        fab.style.display = 'none';
    }}
}}

function saveAllNotes() {{
    fetch('/api/save_notes', {{
        method: 'POST',
        headers: {{ 'Content-Type': 'application/json' }},
        body: JSON.stringify({{ notes: noteState.notes }})
    }}).then(r => r.json()).then(d => {{
        alert('已保存 ' + d.count + ' 条标注笔记');
    }});
}}

function confirmWithNotes() {{
    fetch('/api/confirm_notes', {{
        method: 'POST',
        headers: {{ 'Content-Type': 'application/json' }},
        body: JSON.stringify({{ notes: noteState.notes }})
    }}).then(r => r.json()).then(d => {{
        closeNotePanel();
        alert('已确认 ' + d.count + ' 条标注，将在后续格式化中应用');
    }});
}}

// Initialize notes from server state
fetch('/api/get_notes').then(r => r.json()).then(d => {{
    noteState.notes = d.notes || [];
    // Mark existing notes on elements
    noteState.notes.forEach(n => {{
        const el = document.querySelector(`.annotatable[data-section="${{n.section}}"][data-idx="${{n.idx}}"]`);
        if (el) {{
            el.classList.add('has-note');
            const badge = el.querySelector('.note-badge');
            if (badge) badge.style.display = 'flex';
        }}
    }});
    updateFabCount();
}}).catch(() => {{}});
</script>

<!-- Note FAB Button -->
<button class="note-fab" id="note-fab" onclick="toggleNotePanel()" title="标注笔记">
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M15.5 3H5a2 2 0 00-2 2v14c0 1.1.9 2 2 2h14a2 2 0 002-2V8.5L15.5 3z"/><polyline points="14,3 14,8 21,8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><line x1="10" y1="9" x2="8" y2="9"/></svg>
    <span class="fab-count" id="note-fab-count" style="display:none;">0</span>
</button>

<!-- Note Overlay -->
<div class="note-overlay" id="note-overlay" onclick="closeNotePanel()"></div>

<!-- Note Panel (slide-in from right) -->
<div class="note-panel" id="note-panel">
    <div class="note-panel-header">
        <h3>标注笔记</h3>
        <button class="note-panel-close" onclick="closeNotePanel()">×</button>
    </div>
    <div class="note-panel-body" id="note-panel-body"></div>
    <div class="note-panel-footer">
        <button class="btn btn-secondary" style="flex:1;" onclick="saveAllNotes()">保存笔记</button>
        <button class="btn btn-primary" style="flex:1;" onclick="confirmWithNotes()">确认标注</button>
    </div>
</div>

<!-- Note Modal (center) -->
<div class="note-modal-overlay" id="note-modal-overlay">
    <div class="note-modal">
        <h3>添加修改建议</h3>
        <div class="note-source-preview" id="note-source-preview"></div>
        <textarea id="note-textarea" placeholder="请输入您的修改建议或备注..."></textarea>
        <div class="note-modal-actions">
            <button class="btn btn-secondary" onclick="closeNoteModal()">取消</button>
            <button class="btn btn-primary" onclick="submitNote()">添加标注</button>
        </div>
    </div>
</div>
</body>
</html>'''
    return html


class PreviewHandler(BaseHTTPRequestHandler):
    def _send_json(self, data, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))

    def _read_body(self):
        length = int(self.headers.get("Content-Length", 0))
        return json.loads(self.rfile.read(length).decode("utf-8")) if length else {}

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/" or parsed.path == "/preview":
            html = build_preview_html(STATE)
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(html.encode("utf-8"))
        elif parsed.path == "/api/get_notes":
            self._send_json({"notes": STATE.notes})
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path == "/confirm":
            data = self._read_body()
            STATE.confirmed = True
            STATE.cover_preserved = data.get("cover_preserved", True)
            STATE.toc_preserved = data.get("toc_preserved", True)
            STATE.edited_config = data
            self._send_json({"status": "ok"})
            threading.Thread(target=lambda: self.server.shutdown(), daemon=True).start()

        elif self.path == "/api/add_note":
            data = self._read_body()
            section = data.get("section", "")
            idx = data.get("idx", -1)
            # Remove existing note for same target
            STATE.notes = [n for n in STATE.notes if not (n.get("section") == section and n.get("idx") == idx)]
            STATE.notes.append(data)
            self._send_json({"status": "ok", "count": len(STATE.notes)})

        elif self.path == "/api/delete_note":
            data = self._read_body()
            section = data.get("section", "")
            idx = data.get("idx", -1)
            STATE.notes = [n for n in STATE.notes if not (n.get("section") == section and n.get("idx") == idx)]
            self._send_json({"status": "ok", "count": len(STATE.notes)})

        elif self.path == "/api/save_notes":
            data = self._read_body()
            STATE.notes = data.get("notes", [])
            # Save to workspace/validated/notes.json
            output_dir = Path("workspace/validated")
            output_dir.mkdir(parents=True, exist_ok=True)
            with open(output_dir / "notes.json", "w", encoding="utf-8") as f:
                json.dump({"notes": STATE.notes}, f, ensure_ascii=False, indent=2)
            print(f"[INFO] Notes saved: {len(STATE.notes)} items to {output_dir / 'notes.json'}")
            self._send_json({"status": "ok", "count": len(STATE.notes), "path": str(output_dir / "notes.json")})

        elif self.path == "/api/confirm_notes":
            data = self._read_body()
            STATE.notes = data.get("notes", [])
            # Save notes and return
            output_dir = Path("workspace/validated")
            output_dir.mkdir(parents=True, exist_ok=True)
            with open(output_dir / "notes.json", "w", encoding="utf-8") as f:
                json.dump({"notes": STATE.notes, "confirmed": True}, f, ensure_ascii=False, indent=2)
            print(f"[INFO] Notes confirmed: {len(STATE.notes)} items")
            self._send_json({"status": "ok", "count": len(STATE.notes)})

        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass


def find_free_port(start=8765, end=8770):
    for port in range(start, end + 1):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("127.0.0.1", port))
                return port
            except OSError:
                continue
    return start


def run_preview(ast_path, template_config_path, source_docx_path=None):
    global STATE
    STATE = PreviewState(ast_path, template_config_path, source_docx_path)

    port = find_free_port()
    server = HTTPServer(("127.0.0.1", port), PreviewHandler)

    url = f"http://127.0.0.1:{port}"
    print(f"[INFO] Preview server starting on: {url}")

    import time
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()

    time.sleep(2)

    print(f"[INFO] Opening browser: {url}")
    webbrowser.open(url)

    server_thread.join()

    result = {
        "user_confirmed": STATE.confirmed,
        "cover_preserved": STATE.cover_preserved,
        "toc_preserved": STATE.toc_preserved,
        "edited_config": STATE.edited_config,
        "notes": STATE.notes
    }

    output_dir = Path("workspace/validated")
    output_dir.mkdir(parents=True, exist_ok=True)

    if STATE.edited_config:
        with open(output_dir / "edited_config.json", "w", encoding="utf-8") as f:
            json.dump(STATE.edited_config, f, ensure_ascii=False, indent=2)
        print(f"[INFO] User edited config saved to: {output_dir / 'edited_config.json'}")

    if STATE.notes:
        with open(output_dir / "notes.json", "w", encoding="utf-8") as f:
            json.dump({"notes": STATE.notes}, f, ensure_ascii=False, indent=2)
        print(f"[INFO] Notes saved: {len(STATE.notes)} items to {output_dir / 'notes.json'}")

    print(f"[INFO] User confirmed: {STATE.confirmed}, Notes: {len(STATE.notes)}")
    return result


if __name__ == "__main__":
    import sys
    if len(sys.argv) >= 3:
        result = run_preview(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else None)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print("Usage: python preview_server.py <ast.json> <template_config.json> [source.docx]")
        print()
        print("Example:")
        print("  python preview_server.py workspace/parsed/document_ast.json workspace/validated/template_config.json workspace/input/input.docx")
