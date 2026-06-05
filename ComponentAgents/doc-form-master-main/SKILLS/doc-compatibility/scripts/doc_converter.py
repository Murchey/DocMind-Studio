import os
import sys
import shutil
import subprocess
import json
from pathlib import Path


class DocConverter:
    """将 .doc 格式文档转换为 .docx 格式"""

    def __init__(self):
        self.methods = [
            ('win32com', self._convert_with_win32com),
            ('libreoffice', self._convert_with_libreoffice),
        ]

    @staticmethod
    def is_doc_format(file_path: str) -> bool:
        path = Path(file_path)
        if not path.exists():
            return False

        ext = path.suffix.lower()
        if ext == '.doc':
            return True
        if ext == '.docx':
            return False

        try:
            with open(file_path, 'rb') as f:
                header = f.read(8)
                if header[:4] == b'\xd0\xcf\x11\xe0':
                    return True
        except Exception:
            pass

        return False

    @staticmethod
    def _check_win32com_available() -> bool:
        try:
            import win32com.client
            return True
        except ImportError:
            return False

    @staticmethod
    def _check_libreoffice_available() -> bool:
        possible_paths = [
            r'C:\Program Files\LibreOffice\program\soffice.exe',
            r'C:\Program Files (x86)\LibreOffice\program\soffice.exe',
        ]
        for p in possible_paths:
            if os.path.exists(p):
                return True

        try:
            result = subprocess.run(
                ['soffice', '--version'],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def _convert_with_win32com(self, input_path: str, output_path: str) -> dict:
        try:
            import win32com.client
            import pythoncom

            pythoncom.CoInitialize()

            word = win32com.client.Dispatch("Word.Application")
            word.Visible = False
            word.DisplayAlerts = False

            try:
                abs_input = str(Path(input_path).resolve())
                abs_output = str(Path(output_path).resolve())

                doc = word.Documents.Open(abs_input)
                doc.SaveAs2(abs_output, FileFormat=16)  # 16 = wdFormatXMLDocument (.docx)
                doc.Close()

                return {
                    'success': True,
                    'output_path': output_path,
                    'method': 'win32com',
                    'file_size': os.path.getsize(output_path)
                }
            finally:
                word.Quit()
                pythoncom.CoUninitialize()

        except Exception as e:
            return {
                'success': False,
                'method': 'win32com',
                'error': str(e)
            }

    def _convert_with_libreoffice(self, input_path: str, output_path: str) -> dict:
        try:
            output_dir = str(Path(output_path).parent)
            abs_input = str(Path(input_path).resolve())

            soffice_paths = [
                r'C:\Program Files\LibreOffice\program\soffice.exe',
                r'C:\Program Files (x86)\LibreOffice\program\soffice.exe',
                'soffice',
            ]

            soffice_cmd = None
            for p in soffice_paths:
                if os.path.exists(p) or p == 'soffice':
                    soffice_cmd = p
                    break

            if not soffice_cmd:
                return {
                    'success': False,
                    'method': 'libreoffice',
                    'error': 'LibreOffice not found'
                }

            result = subprocess.run(
                [soffice_cmd, '--headless', '--convert-to', 'docx', '--outdir', output_dir, abs_input],
                capture_output=True,
                text=True,
                timeout=120
            )

            if result.returncode == 0:
                input_stem = Path(input_path).stem
                generated_file = Path(output_dir) / f"{input_stem}.docx"

                if generated_file.exists() and str(generated_file) != str(output_path):
                    shutil.move(str(generated_file), output_path)

                return {
                    'success': True,
                    'output_path': output_path,
                    'method': 'libreoffice',
                    'file_size': os.path.getsize(output_path)
                }
            else:
                return {
                    'success': False,
                    'method': 'libreoffice',
                    'error': result.stderr or result.stdout
                }

        except Exception as e:
            return {
                'success': False,
                'method': 'libreoffice',
                'error': str(e)
            }

    def convert(self, input_path: str, output_path: str = None) -> dict:
        if not os.path.exists(input_path):
            return {
                'success': False,
                'error': f'Input file not found: {input_path}'
            }

        if not self.is_doc_format(input_path):
            return {
                'success': True,
                'input_path': input_path,
                'output_path': input_path,
                'method': 'none',
                'message': 'File is already in .docx format or not a .doc file'
            }

        if output_path is None:
            output_path = str(Path(input_path).with_suffix('.docx'))

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        for method_name, method_func in self.methods:
            print(f"[INFO] Trying conversion method: {method_name}")
            result = method_func(input_path, output_path)
            if result['success']:
                print(f"[INFO] Conversion successful using {method_name}")
                result['input_path'] = input_path
                return result
            else:
                print(f"[WARN] Method {method_name} failed: {result.get('error', 'Unknown error')}")

        return {
            'success': False,
            'input_path': input_path,
            'error': 'All conversion methods failed. Please install Microsoft Word or LibreOffice.'
        }

    def run(self, input_path: str, output_path: str = None) -> dict:
        return self.convert(input_path, output_path)


def main():
    if len(sys.argv) < 2:
        print("Usage: python doc_converter.py <input_doc_path> [output_docx_path]")
        sys.exit(1)

    input_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else None

    converter = DocConverter()
    result = converter.convert(input_path, output_path)

    print(json.dumps(result, indent=2, ensure_ascii=False))

    if not result['success']:
        sys.exit(1)


if __name__ == '__main__':
    main()
