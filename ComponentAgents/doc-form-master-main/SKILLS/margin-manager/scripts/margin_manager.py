import os
import json
import sys
from pathlib import Path
from docx import Document
from docx.shared import Cm, Emu


MARGIN_STANDARDS = {
    'government': {
        'name': '党政机关公文标准（GB/T 9704-2012）',
        'top': 3.7,
        'bottom': 3.5,
        'left': 2.8,
        'right': 2.6,
        'page_width': 21.0,
        'page_height': 29.7,
        'chars_per_line': 28,
        'lines_per_page': 22,
    },
    'academic': {
        'name': '国内学术论文标准',
        'top': 2.54,
        'bottom': 2.54,
        'left': 3.17,
        'right': 3.17,
        'page_width': 21.0,
        'page_height': 29.7,
    },
    'mirror': {
        'name': '镜像页边距（奇偶页不同）',
        'top': 2.54,
        'bottom': 2.54,
        'left': 2.5,
        'right': 2.0,
        'page_width': 21.0,
        'page_height': 29.7,
    },
}


class MarginManager:
    def __init__(self):
        self.standards = MARGIN_STANDARDS

    def get_standard(self, standard_name: str) -> dict:
        if standard_name in self.standards:
            return self.standards[standard_name]
        return None

    def list_standards(self) -> list:
        return [
            {
                'id': key,
                'name': value['name'],
                'margins': {
                    'top': value['top'],
                    'bottom': value['bottom'],
                    'left': value['left'],
                    'right': value['right'],
                }
            }
            for key, value in self.standards.items()
        ]

    def apply_margins(self, docx_path: str, standard: str = None,
                      margins: dict = None, output_path: str = None) -> dict:
        if not os.path.exists(docx_path):
            return {
                'success': False,
                'error': f'File not found: {docx_path}'
            }

        if margins is None:
            if standard is None:
                standard = 'academic'

            std_config = self.get_standard(standard)
            if std_config is None:
                print(f"[WARN] Unknown standard '{standard}', using 'academic'")
                standard = 'academic'
                std_config = self.get_standard(standard)

            margins = {
                'top': std_config['top'],
                'bottom': std_config['bottom'],
                'left': std_config['left'],
                'right': std_config['right'],
            }

        if output_path is None:
            output_path = docx_path

        try:
            doc = Document(docx_path)
            sections_modified = 0

            for section in doc.sections:
                section.top_margin = Cm(margins['top'])
                section.bottom_margin = Cm(margins['bottom'])
                section.left_margin = Cm(margins['left'])
                section.right_margin = Cm(margins['right'])
                sections_modified += 1

            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            doc.save(output_path)

            result = {
                'success': True,
                'docx_path': output_path,
                'standard': standard,
                'margins': margins,
                'sections_modified': sections_modified,
            }

            if standard:
                std_config = self.get_standard(standard)
                if std_config:
                    result['standard_name'] = std_config['name']

            print(f"[INFO] Margins applied: {margins} ({sections_modified} sections)")
            return result

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def get_current_margins(self, docx_path: str) -> dict:
        if not os.path.exists(docx_path):
            return {
                'success': False,
                'error': f'File not found: {docx_path}'
            }

        try:
            doc = Document(docx_path)
            sections = []

            for i, section in enumerate(doc.sections):
                sections.append({
                    'index': i,
                    'top': round(section.top_margin / 360000, 2),
                    'bottom': round(section.bottom_margin / 360000, 2),
                    'left': round(section.left_margin / 360000, 2),
                    'right': round(section.right_margin / 360000, 2),
                })

            return {
                'success': True,
                'docx_path': docx_path,
                'sections': sections,
                'total_sections': len(sections),
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def run(self, docx_path: str, standard: str = None,
            margins: dict = None, output_path: str = None) -> dict:
        return self.apply_margins(docx_path, standard, margins, output_path)


def main():
    if len(sys.argv) < 2:
        print("Usage: python margin_manager.py <docx_path> [standard]")
        print("Standards: government, academic, mirror")
        sys.exit(1)

    docx_path = sys.argv[1]
    standard = sys.argv[2] if len(sys.argv) > 2 else 'academic'

    manager = MarginManager()

    result = manager.apply_margins(docx_path, standard=standard)
    print(json.dumps(result, indent=2, ensure_ascii=False))

    if not result['success']:
        sys.exit(1)


if __name__ == '__main__':
    main()
