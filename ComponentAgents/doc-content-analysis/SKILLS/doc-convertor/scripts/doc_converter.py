import os
import sys
import json
import shutil
import subprocess
from pathlib import Path


class DocConverter:
    """DOC/DOCX/PDF 文档转换与内容提取，支持单文件和批量处理。"""

    def __init__(self):
        self.doc_methods = [
            ('win32com', self._convert_doc_with_win32com),
            ('libreoffice', self._convert_with_libreoffice),
        ]

    # ── 格式检测 ──────────────────────────────────────────────

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
    def is_pdf_format(file_path: str) -> bool:
        path = Path(file_path)
        if not path.exists():
            return False
        if path.suffix.lower() == '.pdf':
            return True
        try:
            with open(file_path, 'rb') as f:
                header = f.read(5)
                return header == b'%PDF-'
        except Exception:
            pass
        return False

    # ── .doc → .docx 转换 ─────────────────────────────────────

    def _convert_doc_with_win32com(self, input_path: str, output_path: str) -> dict:
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
                doc.SaveAs2(abs_output, FileFormat=16)
                doc.Close()
                return {
                    'success': True, 'output_path': output_path,
                    'method': 'win32com', 'file_size': os.path.getsize(output_path)
                }
            finally:
                word.Quit()
                pythoncom.CoUninitialize()
        except Exception as e:
            return {'success': False, 'method': 'win32com', 'error': str(e)}

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
                return {'success': False, 'method': 'libreoffice', 'error': 'LibreOffice not found'}
            result = subprocess.run(
                [soffice_cmd, '--headless', '--convert-to', 'docx', '--outdir', output_dir, abs_input],
                capture_output=True, text=True, timeout=120
            )
            if result.returncode == 0:
                input_stem = Path(input_path).stem
                generated_file = Path(output_dir) / f"{input_stem}.docx"
                if generated_file.exists() and str(generated_file) != str(output_path):
                    shutil.move(str(generated_file), output_path)
                return {
                    'success': True, 'output_path': output_path,
                    'method': 'libreoffice', 'file_size': os.path.getsize(output_path)
                }
            else:
                return {'success': False, 'method': 'libreoffice', 'error': result.stderr or result.stdout}
        except Exception as e:
            return {'success': False, 'method': 'libreoffice', 'error': str(e)}

    def convert_doc(self, input_path: str, output_path: str = None) -> dict:
        if not os.path.exists(input_path):
            return {'success': False, 'error': f'Input file not found: {input_path}'}
        if not self.is_doc_format(input_path):
            return {
                'success': True, 'input_path': input_path,
                'output_path': input_path, 'method': 'none',
                'message': 'File is already in .docx format or not a .doc file'
            }
        if output_path is None:
            output_path = str(Path(input_path).with_suffix('.docx'))
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        for method_name, method_func in self.doc_methods:
            print(f"[INFO] Trying .doc conversion method: {method_name}")
            result = method_func(input_path, output_path)
            if result['success']:
                print(f"[INFO] Conversion successful using {method_name}")
                result['input_path'] = input_path
                return result
            else:
                print(f"[WARN] Method {method_name} failed: {result.get('error', 'Unknown error')}")
        return {
            'success': False, 'input_path': input_path,
            'error': 'All conversion methods failed. Please install Microsoft Word or LibreOffice.'
        }

    # ── PDF → DOCX 转换 ──────────────────────────────────────

    def convert_pdf(self, input_path: str, output_path: str = None) -> dict:
        if not os.path.exists(input_path):
            return {'success': False, 'error': f'Input file not found: {input_path}'}
        if not self.is_pdf_format(input_path):
            return {'success': False, 'error': f'Not a PDF file: {input_path}'}
        if output_path is None:
            output_path = str(Path(input_path).with_suffix('.docx'))
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        try:
            from pdf2docx import Converter
            print(f"[INFO] Converting PDF to DOCX: {Path(input_path).name}")
            cv = Converter(input_path)
            cv.convert(output_path)
            cv.close()
            print(f"[INFO] PDF conversion successful")
            return {
                'success': True, 'input_path': input_path,
                'output_path': output_path, 'method': 'pdf2docx',
                'file_size': os.path.getsize(output_path)
            }
        except ImportError:
            return {
                'success': False, 'input_path': input_path,
                'error': 'pdf2docx not installed. Run: pip install pdf2docx'
            }
        except Exception as e:
            return {
                'success': False, 'input_path': input_path,
                'method': 'pdf2docx', 'error': str(e)
            }

    # ── 统一转换入口 ──────────────────────────────────────────

    def convert(self, input_path: str, output_path: str = None) -> dict:
        if not os.path.exists(input_path):
            return {'success': False, 'error': f'Input file not found: {input_path}'}
        if self.is_pdf_format(input_path):
            return self.convert_pdf(input_path, output_path)
        if self.is_doc_format(input_path):
            return self.convert_doc(input_path, output_path)
        ext = Path(input_path).suffix.lower()
        if ext == '.docx':
            return {
                'success': True, 'input_path': input_path,
                'output_path': input_path, 'method': 'none',
                'message': 'Already .docx format'
            }
        return {'success': False, 'error': f'Unsupported format: {ext}'}

    def batch_convert(self, input_dir: str, output_dir: str = None) -> list:
        if output_dir is None:
            output_dir = input_dir
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        results = []
        # .doc files
        doc_files = sorted(Path(input_dir).glob('*.doc'))
        doc_files = [f for f in doc_files if f.suffix.lower() == '.doc' and not f.name.startswith('~')]
        for doc_file in doc_files:
            output_path = str(Path(output_dir) / doc_file.with_suffix('.docx').name)
            print(f"[INFO] Converting .doc: {doc_file.name}")
            result = self.convert_doc(str(doc_file), output_path)
            result['input'] = str(doc_file)
            results.append(result)
        # .pdf files
        pdf_files = sorted(Path(input_dir).glob('*.pdf'))
        pdf_files = [f for f in pdf_files if not f.name.startswith('~')]
        for pdf_file in pdf_files:
            output_path = str(Path(output_dir) / pdf_file.with_suffix('.docx').name)
            print(f"[INFO] Converting PDF: {pdf_file.name}")
            result = self.convert_pdf(str(pdf_file), output_path)
            result['input'] = str(pdf_file)
            results.append(result)
        # .docx files (copy)
        docx_files = sorted(Path(input_dir).glob('*.docx'))
        docx_files = [f for f in docx_files if not f.name.startswith('~')]
        for docx_file in docx_files:
            target_path = str(Path(output_dir) / docx_file.name)
            if str(docx_file) != target_path:
                shutil.copy2(str(docx_file), target_path)
            results.append({
                'success': True, 'input': str(docx_file),
                'output_path': target_path, 'method': 'copy',
                'message': 'Already .docx format'
            })
        return results

    # ── 内容提取（文本 + 表格） ───────────────────────────────

    def extract_content(self, docx_path: str) -> dict:
        if not os.path.exists(docx_path):
            return {'success': False, 'error': f'File not found: {docx_path}'}
        try:
            from docx import Document
        except ImportError:
            return {'success': False, 'error': 'python-docx not installed. Run: pip install python-docx'}
        try:
            doc = Document(docx_path)
            core = doc.core_properties
            paragraphs = []
            full_text_parts = []
            for para in doc.paragraphs:
                text = para.text.strip()
                if not text:
                    continue
                style_name = para.style.name if para.style else 'Normal'
                is_heading = style_name.startswith('Heading')
                level = 0
                if is_heading:
                    try:
                        level = int(style_name.replace('Heading ', ''))
                    except ValueError:
                        level = 0
                paragraphs.append({
                    'text': text, 'style': style_name,
                    'is_heading': is_heading, 'level': level
                })
                full_text_parts.append(text)
            tables = []
            for table in doc.tables:
                rows = []
                for row in table.rows:
                    cells = [cell.text.strip() for cell in row.cells]
                    rows.append(cells)
                if rows:
                    tables.append({'rows': rows})
                for row in rows:
                    full_text_parts.append('\t'.join(row))
            return {
                'success': True,
                'file_name': Path(docx_path).name,
                'file_path': str(docx_path),
                'title': core.title or Path(docx_path).stem,
                'author': core.author or '',
                'created_at': str(core.created) if core.created else '',
                'paragraph_count': len(paragraphs),
                'table_count': len(tables),
                'paragraphs': paragraphs,
                'tables': tables,
                'full_text': '\n'.join(full_text_parts)
            }
        except Exception as e:
            return {'success': False, 'error': f'Failed to extract content: {str(e)}'}

    # ── 图片提取 ──────────────────────────────────────────────

    def extract_images(self, docx_path: str, output_dir: str) -> dict:
        if not os.path.exists(docx_path):
            return {'success': False, 'error': f'File not found: {docx_path}'}
        try:
            from docx import Document
            from docx.opc.constants import RELATIONSHIP_TYPE as RT
        except ImportError:
            return {'success': False, 'error': 'python-docx not installed. Run: pip install python-docx'}
        try:
            doc = Document(docx_path)
            Path(output_dir).mkdir(parents=True, exist_ok=True)
            saved = []
            idx = 0
            for rel in doc.part.rels.values():
                if "image" in rel.reltype:
                    idx += 1
                    image_data = rel.target_part.blob
                    ext = Path(rel.target_ref).suffix.lower()
                    if ext not in ('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.emf', '.wmf'):
                        ext = '.png'
                    out_name = f"image_{idx}{ext}"
                    out_path = Path(output_dir) / out_name
                    with open(out_path, 'wb') as f:
                        f.write(image_data)
                    saved.append(str(out_path))
            print(f"[INFO] Extracted {len(saved)} image(s) from {Path(docx_path).name}")
            return {
                'success': True,
                'source': str(docx_path),
                'output_dir': str(output_dir),
                'image_count': len(saved),
                'images': saved
            }
        except Exception as e:
            return {'success': False, 'error': f'Failed to extract images: {str(e)}'}

    # ── .txt 内容提取 ─────────────────────────────────────────

    def extract_txt_content(self, txt_path: str) -> dict:
        if not os.path.exists(txt_path):
            return {'success': False, 'error': f'File not found: {txt_path}'}
        try:
            text = Path(txt_path).read_text(encoding='utf-8')
        except UnicodeDecodeError:
            try:
                text = Path(txt_path).read_text(encoding='gbk')
            except Exception:
                text = Path(txt_path).read_text(encoding='utf-8', errors='ignore')
        lines = [l.strip() for l in text.splitlines() if l.strip()]
        return {
            'success': True,
            'file_name': Path(txt_path).name,
            'file_path': str(txt_path),
            'title': Path(txt_path).stem,
            'author': '',
            'created_at': '',
            'paragraph_count': len(lines),
            'table_count': 0,
            'paragraphs': [
                {'text': l, 'style': 'Normal', 'is_heading': False, 'level': 0}
                for l in lines
            ],
            'tables': [],
            'full_text': text
        }

    # ── 批量提取 ──────────────────────────────────────────────

    def extract_batch(self, input_dir: str) -> list:
        results = []
        docx_files = sorted(Path(input_dir).glob('*.docx'))
        docx_files = [f for f in docx_files if not f.name.startswith('~')]
        for docx_file in docx_files:
            print(f"[INFO] Extracting content: {docx_file.name}")
            content = self.extract_content(str(docx_file))
            results.append(content)
        return results

    # ── 全流程处理 ────────────────────────────────────────────

    def process_all(self, input_dir: str, workspace_dir: str) -> dict:
        input_dir = str(Path(input_dir).resolve())
        workspace_dir = str(Path(workspace_dir).resolve())
        converted_dir = str(Path(workspace_dir) / 'converted')
        summary_dir = str(Path(workspace_dir) / 'summary')
        logs_dir = str(Path(workspace_dir) / 'logs')

        for d in [converted_dir, summary_dir, logs_dir]:
            Path(d).mkdir(parents=True, exist_ok=True)

        # 空输入检查
        input_files = []
        for ext in ['*.doc', '*.docx', '*.pdf', '*.txt']:
            input_files.extend(Path(input_dir).glob(ext))
        input_files = sorted([f for f in input_files if not f.name.startswith('~')])

        if not input_files:
            print(f"[WARN] No supported files found in {input_dir}")
            return {
                'status': 'empty',
                'convert_results': [],
                'summaries': [],
                'converted_dir': converted_dir,
                'summary_dir': summary_dir,
            }

        convert_results = self.batch_convert(input_dir, converted_dir)

        docx_files = sorted(Path(converted_dir).glob('*.docx'))
        docx_files = [f for f in docx_files if not f.name.startswith('~')]

        # 处理 .txt 文件（直接提取，不需要转换）
        txt_files = sorted(Path(input_dir).glob('*.txt'))
        txt_files = [f for f in txt_files if not f.name.startswith('~')]

        summaries = []
        for docx_file in docx_files:
            stem = docx_file.stem
            doc_summary_dir = Path(summary_dir) / stem
            text_dir = doc_summary_dir / 'text'
            img_dir = doc_summary_dir / 'img'
            text_dir.mkdir(parents=True, exist_ok=True)
            img_dir.mkdir(parents=True, exist_ok=True)

            content = self.extract_content(str(docx_file))
            if content.get('success'):
                content_path = text_dir / 'content.json'
                with open(content_path, 'w', encoding='utf-8') as f:
                    json.dump(content, f, indent=2, ensure_ascii=False)

            img_result = self.extract_images(str(docx_file), str(img_dir))

            summaries.append({
                'file_name': stem,
                'source_file': docx_file.name,
                'docx_path': str(docx_file),
                'text_dir': str(text_dir),
                'img_dir': str(img_dir),
                'content_success': content.get('success', False),
                'image_count': img_result.get('image_count', 0),
            })

        for txt_file in txt_files:
            stem = txt_file.stem
            doc_summary_dir = Path(summary_dir) / stem
            text_dir = doc_summary_dir / 'text'
            text_dir.mkdir(parents=True, exist_ok=True)

            content = self.extract_txt_content(str(txt_file))
            if content.get('success'):
                content_path = text_dir / 'content.json'
                with open(content_path, 'w', encoding='utf-8') as f:
                    json.dump(content, f, indent=2, ensure_ascii=False)

            summaries.append({
                'file_name': stem,
                'source_file': txt_file.name,
                'docx_path': None,
                'text_dir': str(text_dir),
                'img_dir': None,
                'content_success': content.get('success', False),
                'image_count': 0,
            })

        return {
            'status': 'completed',
            'convert_results': convert_results,
            'summaries': summaries,
            'converted_dir': converted_dir,
            'summary_dir': summary_dir,
        }


def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python doc_converter.py convert <input_path> [output_path]")
        print("  python doc_converter.py batch_convert <input_dir> [output_dir]")
        print("  python doc_converter.py extract <docx_path>")
        print("  python doc_converter.py extract_batch <input_dir>")
        print("  python doc_converter.py extract_images <docx_path> <output_dir>")
        print("  python doc_converter.py process_all <input_dir> <workspace_dir>")
        sys.exit(1)

    cmd = sys.argv[1]
    converter = DocConverter()

    if cmd == 'convert':
        if len(sys.argv) < 3:
            print("Error: input_path required")
            sys.exit(1)
        result = converter.convert(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else None)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        if not result['success']:
            sys.exit(1)

    elif cmd == 'batch_convert':
        if len(sys.argv) < 3:
            print("Error: input_dir required")
            sys.exit(1)
        results = converter.batch_convert(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else None)
        print(json.dumps(results, indent=2, ensure_ascii=False))

    elif cmd == 'extract':
        if len(sys.argv) < 3:
            print("Error: docx_path required")
            sys.exit(1)
        result = converter.extract_content(sys.argv[2])
        print(json.dumps(result, indent=2, ensure_ascii=False))

    elif cmd == 'extract_batch':
        if len(sys.argv) < 3:
            print("Error: input_dir required")
            sys.exit(1)
        results = converter.extract_batch(sys.argv[2])
        print(json.dumps(results, indent=2, ensure_ascii=False))

    elif cmd == 'extract_images':
        if len(sys.argv) < 4:
            print("Error: docx_path and output_dir required")
            sys.exit(1)
        result = converter.extract_images(sys.argv[2], sys.argv[3])
        print(json.dumps(result, indent=2, ensure_ascii=False))

    elif cmd == 'process_all':
        if len(sys.argv) < 4:
            print("Error: input_dir and workspace_dir required")
            sys.exit(1)
        result = converter.process_all(sys.argv[2], sys.argv[3])
        print(json.dumps(result, indent=2, ensure_ascii=False))

    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)


if __name__ == '__main__':
    main()
