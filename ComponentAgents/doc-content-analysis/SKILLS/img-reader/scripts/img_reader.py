import os
import sys
import json
from pathlib import Path


class ImgReader:
    """图片 OCR 文字识别，支持多种 OCR 引擎。"""

    IMAGE_EXTS = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.tif', '.webp'}

    def __init__(self):
        self._ocr_engine = None
        self._engine_name = None

    def _init_ocr(self):
        if self._ocr_engine is not None:
            return

        # Priority 1: PaddleOCR (best for Chinese)
        try:
            from paddleocr import PaddleOCR
            self._ocr_engine = PaddleOCR(use_angle_cls=True, lang='ch', show_log=False)
            self._engine_name = 'paddleocr'
            print("[INFO] OCR engine: PaddleOCR")
            return
        except (ImportError, Exception):
            pass

        # Priority 2: EasyOCR
        try:
            import easyocr
            self._ocr_engine = easyocr.Reader(['ch_sim', 'en'], gpu=False)
            self._engine_name = 'easyocr'
            print("[INFO] OCR engine: EasyOCR")
            return
        except (ImportError, Exception):
            pass

        # Priority 3: Tesseract
        try:
            import pytesseract
            pytesseract.get_tesseract_version()
            self._ocr_engine = 'tesseract'
            self._engine_name = 'tesseract'
            print("[INFO] OCR engine: Tesseract")
            return
        except Exception:
            pass

        self._ocr_engine = None
        self._engine_name = None
        print("[WARN] No OCR engine available. Install one of: paddleocr, easyocr, pytesseract")

    def extract_text(self, image_path: str) -> dict:
        if not os.path.exists(image_path):
            return {'success': False, 'error': f'Image not found: {image_path}'}

        ext = Path(image_path).suffix.lower()
        if ext not in self.IMAGE_EXTS:
            return {'success': False, 'error': f'Unsupported image format: {ext}'}

        self._init_ocr()

        if self._ocr_engine is None:
            return {
                'success': False,
                'image_path': str(image_path),
                'error': 'No OCR engine available'
            }

        try:
            text = self._run_ocr(image_path)
            text = text.strip()
            return {
                'success': True,
                'image_path': str(image_path),
                'has_text': len(text) > 0,
                'text': text,
                'text_length': len(text),
                'engine': self._engine_name
            }
        except Exception as e:
            return {
                'success': False,
                'image_path': str(image_path),
                'error': f'OCR failed: {str(e)}'
            }

    def _run_ocr(self, image_path: str) -> str:
        if self._engine_name == 'paddleocr':
            result = self._ocr_engine.ocr(image_path, cls=True)
            if not result or not result[0]:
                return ''
            lines = []
            for line in result[0]:
                if line and len(line) >= 2:
                    text = line[1][0] if isinstance(line[1], (list, tuple)) else str(line[1])
                    lines.append(text)
            return '\n'.join(lines)

        elif self._engine_name == 'easyocr':
            result = self._ocr_engine.readtext(image_path)
            lines = []
            for item in result:
                if len(item) >= 2:
                    lines.append(str(item[1]))
            return '\n'.join(lines)

        elif self._engine_name == 'tesseract':
            import pytesseract
            from PIL import Image
            img = Image.open(image_path)
            text = pytesseract.image_to_string(img, lang='chi_sim+eng')
            return text

        return ''

    def process_batch(self, img_dir: str, text_dir: str, summary_dir: str) -> dict:
        img_dir = Path(img_dir)
        if not img_dir.exists():
            return {'success': False, 'error': f'Image directory not found: {img_dir}'}

        text_path = Path(text_dir)
        summary_path = Path(summary_dir)
        text_path.mkdir(parents=True, exist_ok=True)
        summary_path.mkdir(parents=True, exist_ok=True)

        image_files = sorted([
            f for f in img_dir.iterdir()
            if f.is_file() and f.suffix.lower() in self.IMAGE_EXTS
        ])

        if not image_files:
            return {
                'success': True,
                'message': 'No images found',
                'img_dir': str(img_dir),
                'results': []
            }

        self._init_ocr()

        results = []
        for img_file in image_files:
            stem = img_file.stem
            print(f"[INFO] Processing image: {img_file.name}")

            ocr_result = self.extract_text(str(img_file))

            # Save OCR text
            txt_path = text_path / f"{stem}.txt"
            if ocr_result.get('success') and ocr_result.get('has_text'):
                with open(txt_path, 'w', encoding='utf-8') as f:
                    f.write(ocr_result['text'])
            else:
                with open(txt_path, 'w', encoding='utf-8') as f:
                    f.write('')

            # Create placeholder summary markdown
            md_path = summary_path / f"{stem}.md"
            ocr_text = ocr_result.get('text', '') if ocr_result.get('has_text') else ''
            with open(md_path, 'w', encoding='utf-8') as f:
                f.write(f"# 图片分析：{img_file.name}\n\n")
                f.write(f"**图片路径**：`{img_file}`\n\n")
                f.write("---\n\n")
                f.write("## 图片描述\n\n")
                f.write("<待 AI 视觉模型填充>\n\n")
                f.write("## 文字内容\n\n")
                if ocr_text:
                    f.write(ocr_text + "\n\n")
                else:
                    f.write("图片中未检测到文字\n\n")
                f.write("## 内容总结\n\n")
                f.write("<待 AI 视觉模型填充>\n\n")
                f.write("---\n")

            results.append({
                'image': str(img_file),
                'ocr_success': ocr_result.get('success', False),
                'has_text': ocr_result.get('has_text', False),
                'text_length': ocr_result.get('text_length', 0),
                'txt_path': str(txt_path),
                'md_path': str(md_path),
            })

        return {
            'success': True,
            'img_dir': str(img_dir),
            'text_dir': str(text_dir),
            'summary_dir': str(summary_dir),
            'image_count': len(image_files),
            'ocr_engine': self._engine_name,
            'results': results
        }


def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python img_reader.py extract_text <image_path>")
        print("  python img_reader.py process_batch <img_dir> <text_dir> <summary_dir>")
        sys.exit(1)

    cmd = sys.argv[1]
    reader = ImgReader()

    if cmd == 'extract_text':
        if len(sys.argv) < 3:
            print("Error: image_path required")
            sys.exit(1)
        result = reader.extract_text(sys.argv[2])
        print(json.dumps(result, indent=2, ensure_ascii=False))

    elif cmd == 'process_batch':
        if len(sys.argv) < 5:
            print("Error: img_dir, text_dir, summary_dir required")
            sys.exit(1)
        result = reader.process_batch(sys.argv[2], sys.argv[3], sys.argv[4])
        print(json.dumps(result, indent=2, ensure_ascii=False))

    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)


if __name__ == '__main__':
    main()
