import zipfile
import shutil
import os
from lxml import etree
from docx import Document
from docx.shared import Pt, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH


W_NS = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
R_NS = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
M_NS = 'http://schemas.openxmlformats.org/officeDocument/2006/math'

NSMAP = {
    'w': W_NS,
    'r': R_NS,
    'm': M_NS,
}

CIRCLED_NUMBERS = [
    '\u2460', '\u2461', '\u2462', '\u2463', '\u2464',
    '\u2465', '\u2466', '\u2467', '\u2468', '\u2469',
    '\u246a', '\u246b', '\u246c', '\u246d', '\u246e',
    '\u246f', '\u2470', '\u2471', '\u2472', '\u2473',
]


class FootnoteProcessor:

    def __init__(self, docx_path, config_path=None):
        self.docx_path = docx_path
        self.config = self._load_config(config_path)
        self.doc = None
        self.footnotes_xml = None
        self.endnotes_xml = None
        self.footnote_count = 0
        self.endnote_count = 0
        self.changes = []

    def _load_config(self, config_path):
        default_config = {
            'enabled': True,
            'font_size_cn': 10.5,
            'font_size_en': 9,
            'line_spacing': 'single',
            'numbering': 'circled',
            'restart_per_page': True,
            'separator_length': 25,
            'font_name_cn': '宋体',
            'font_name_en': 'Times New Roman',
            'first_line_indent': 0,
        }

        if config_path and os.path.exists(config_path):
            import yaml
            with open(config_path, 'r', encoding='utf-8') as f:
                full_config = yaml.safe_load(f)
                if 'footnote' in full_config:
                    default_config.update(full_config['footnote'])

        if 'font_size' in default_config and 'font_size_cn' not in default_config:
            default_config['font_size_cn'] = default_config['font_size']
            default_config['font_size_en'] = default_config['font_size'] - 1

        return default_config

    def _extract_xml(self):
        with zipfile.ZipFile(self.docx_path, 'r') as zip_ref:
            if 'word/footnotes.xml' in zip_ref.namelist():
                self.footnotes_xml = zip_ref.read('word/footnotes.xml')
            if 'word/endnotes.xml' in zip_ref.namelist():
                self.endnotes_xml = zip_ref.read('word/endnotes.xml')

    def _format_footnotes(self):
        if not self.footnotes_xml:
            return

        root = etree.fromstring(self.footnotes_xml)
        footnotes = root.findall(f'{{{W_NS}}}footnote')

        for footnote in footnotes:
            footnote_id = footnote.get(f'{{{W_NS}}}id')
            self._format_note_content(footnote, 'footnote')
            self.footnote_count += 1

        if self.config['restart_per_page']:
            self._set_restart_per_page(root, 'footnote')

        self.footnotes_xml = etree.tostring(root, xml_declaration=True, encoding='UTF-8', standalone=True)

    def _format_endnotes(self):
        if not self.endnotes_xml:
            return

        root = etree.fromstring(self.endnotes_xml)
        endnotes = root.findall(f'{{{W_NS}}}endnote')

        for endnote in endnotes:
            endnote_id = endnote.get(f'{{{W_NS}}}id')
            self._format_note_content(endnote, 'endnote')
            self.endnote_count += 1

        self.endnotes_xml = etree.tostring(root, xml_declaration=True, encoding='UTF-8', standalone=True)

    def _set_restart_per_page(self, root, note_type):
        sect_pr = root.find(f'{{{W_NS}}}sectPr')
        if sect_pr is None:
            sect_pr = etree.SubElement(root, f'{{{W_NS}}}sectPr')

        footnote_pr = sect_pr.find(f'{{{W_NS}}}footnotePr')
        if footnote_pr is None:
            footnote_pr = etree.SubElement(sect_pr, f'{{{W_NS}}}footnotePr')

        num_fmt = footnote_pr.find(f'{{{W_NS}}}numFmt')
        if num_fmt is None:
            num_fmt = etree.SubElement(footnote_pr, f'{{{W_NS}}}numFmt')
        num_fmt.set(f'{{{W_NS}}}val', 'decimal')

        num_restart = footnote_pr.find(f'{{{W_NS}}}numRestart')
        if num_restart is None:
            num_restart = etree.SubElement(footnote_pr, f'{{{W_NS}}}numRestart')
        num_restart.set(f'{{{W_NS}}}val', 'eachPage')

    def _format_note_content(self, note_elem, note_type):
        paragraphs = note_elem.findall(f'{{{W_NS}}}p')

        for para in paragraphs:
            self._format_paragraph(para)

    def _format_paragraph(self, para_elem):
        font_size_cn = self.config['font_size_cn']
        font_size_en = self.config['font_size_en']
        line_spacing = self.config['line_spacing']
        first_line_indent = self.config['first_line_indent']

        ppr = para_elem.find(f'{{{W_NS}}}pPr')
        if ppr is None:
            ppr = etree.SubElement(para_elem, f'{{{W_NS}}}pPr')
            para_elem.insert(0, ppr)

        spacing = ppr.find(f'{{{W_NS}}}spacing')
        if spacing is None:
            spacing = etree.SubElement(ppr, f'{{{W_NS}}}spacing')

        if line_spacing == 'single':
            spacing.set(f'{{{W_NS}}}line', '240')
            spacing.set(f'{{{W_NS}}}lineRule', 'auto')
        elif line_spacing == '1.5':
            spacing.set(f'{{{W_NS}}}line', '360')
            spacing.set(f'{{{W_NS}}}lineRule', 'auto')
        elif line_spacing == 'double':
            spacing.set(f'{{{W_NS}}}line', '480')
            spacing.set(f'{{{W_NS}}}lineRule', 'auto')

        ind = ppr.find(f'{{{W_NS}}}ind')
        if ind is not None:
            ppr.remove(ind)

        if first_line_indent > 0:
            ind = etree.SubElement(ppr, f'{{{W_NS}}}ind')
            ind.set(f'{{{W_NS}}}firstLine', str(int(first_line_indent * 20)))

        runs = para_elem.findall(f'{{{W_NS}}}r')
        for run in runs:
            self._format_run(run)

    def _format_run(self, run_elem):
        font_size_cn = self.config['font_size_cn']
        font_size_en = self.config['font_size_en']
        font_name_cn = self.config['font_name_cn']
        font_name_en = self.config['font_name_en']

        rpr = run_elem.find(f'{{{W_NS}}}rPr')
        if rpr is None:
            rpr = etree.SubElement(run_elem, f'{{{W_NS}}}rPr')
            run_elem.insert(0, rpr)

        text_elem = run_elem.find(f'{{{W_NS}}}t')
        is_cjk = False
        if text_elem is not None and text_elem.text:
            is_cjk = any('\u4e00' <= c <= '\u9fff' for c in text_elem.text)

        sz = rpr.find(f'{{{W_NS}}}sz')
        if sz is None:
            sz = etree.SubElement(rpr, f'{{{W_NS}}}sz')
        sz.set(f'{{{W_NS}}}val', str(int(font_size_cn * 2)))

        szCs = rpr.find(f'{{{W_NS}}}szCs')
        if szCs is None:
            szCs = etree.SubElement(rpr, f'{{{W_NS}}}szCs')
        szCs.set(f'{{{W_NS}}}val', str(int(font_size_en * 2)))

        rFonts = rpr.find(f'{{{W_NS}}}rFonts')
        if rFonts is None:
            rFonts = etree.SubElement(rpr, f'{{{W_NS}}}rFonts')
        rFonts.set(f'{{{W_NS}}}ascii', font_name_en)
        rFonts.set(f'{{{W_NS}}}hAnsi', font_name_en)
        rFonts.set(f'{{{W_NS}}}eastAsia', font_name_cn)

    def _save_xml(self, output_path):
        with zipfile.ZipFile(self.docx_path, 'r') as zip_in:
            with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zip_out:
                for item in zip_in.infolist():
                    if item.filename == 'word/footnotes.xml' and self.footnotes_xml:
                        zip_out.writestr(item, self.footnotes_xml)
                    elif item.filename == 'word/endnotes.xml' and self.endnotes_xml:
                        zip_out.writestr(item, self.endnotes_xml)
                    else:
                        zip_out.writestr(item, zip_in.read(item.filename))

    def run(self):
        if not self.config['enabled']:
            print("[INFO] Footnote processing disabled")
            return

        print("[INFO] Starting footnote processing...")
        self._extract_xml()

        if self.footnotes_xml:
            self._format_footnotes()
            print(f"[INFO] Formatted {self.footnote_count} footnotes")

        if self.endnotes_xml:
            self._format_endnotes()
            print(f"[INFO] Formatted {self.endnote_count} endnotes")

        if self.footnotes_xml or self.endnotes_xml:
            temp_path = self.docx_path + '.tmp'
            self._save_xml(temp_path)
            shutil.move(temp_path, self.docx_path)
            print("[INFO] Footnote processing completed")
        else:
            print("[INFO] No footnotes or endnotes found")

    def save(self, output_path):
        if self.footnotes_xml or self.endnotes_xml:
            self._save_xml(output_path)
            print(f"[INFO] Saved to {output_path}")
        else:
            shutil.copy2(self.docx_path, output_path)
            print("[INFO] No footnotes to process, copied original file")

    def get_report(self):
        return {
            'footnote_count': self.footnote_count,
            'endnote_count': self.endnote_count,
            'changes': self.changes,
            'config': self.config,
        }


if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
        print("Usage: python footnote_processor.py <docx_path> [config_path]")
        sys.exit(1)

    docx_path = sys.argv[1]
    config_path = sys.argv[2] if len(sys.argv) > 2 else None

    processor = FootnoteProcessor(docx_path, config_path)
    processor.run()
    report = processor.get_report()
    print(f"\nReport: {report}")
