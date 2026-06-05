import os
import re
import sys
import json
import shutil
import subprocess
from pathlib import Path


class MathFormulaProcessor:
    LATEX_PATTERNS = [
        r'\\[a-zA-Z]+(?:\{[^}]*\})*',
        r'\^{(?:[^}]*)}',
        r'_(?:{[^}]*}|[a-zA-Z0-9])',
        r'\\frac(?:{[^}]*}){2}',
        r'\\sqrt(?:{[^}]*})?',
        r'\\(?:int|sum|prod|lim|inf|sup|min|max)',
        r'\\(?:sin|cos|tan|cot|sec|csc|log|ln|exp)',
        r'\\(?:le|ge|neq|approx|equiv|sim|propto)',
        r'\\(?:alpha|beta|gamma|delta|epsilon|zeta|eta|theta|iota|kappa|lambda|mu|nu|xi|pi|rho|sigma|tau|upsilon|phi|chi|psi|omega)',
        r'\\(?:Alpha|Beta|Gamma|Delta|Epsilon|Zeta|Eta|Theta|Iota|Kappa|Lambda|Mu|Nu|Xi|Pi|Rho|Sigma|Tau|Upsilon|Phi|Chi|Psi|Omega)',
        r'\\(?:partial|nabla|infty|emptyset|forall|exists|in|notin|subset|supset|cap|cup)',
        r'\\(?:rightarrow|leftarrow|Rightarrow|Leftarrow|leftrightarrow|Leftrightarrow)',
        r'\\(?:pm|mp|times|cdot|div|circ|bullet|star|dagger)',
        r'\\(?:ldots|cdots|vdots|ddots)',
        r'\\(?:quad|qquad|hspace|vspace)',
        r'\\(?:text|mathrm|mathbf|mathit|mathcal|mathbb|mathfrak)',
        r'\\(?:left|right|Big|big|bigg|Bigg)',
        r'\\(?:overline|underline|hat|tilde|bar|vec|dot|ddot)',
    ]

    @classmethod
    def has_latex(cls, text: str) -> bool:
        for pattern in cls.LATEX_PATTERNS:
            if re.search(pattern, text):
                return True
        return False

    @classmethod
    def is_already_formatted(cls, text: str) -> bool:
        return bool(re.search(r'\$.*?\$', text))

    @classmethod
    def format_formulas(cls, text: str) -> str:
        if cls.is_already_formatted(text):
            return text

        if not cls.has_latex(text):
            return text

        result = text

        for pattern in cls.LATEX_PATTERNS:
            matches = list(re.finditer(pattern, result))
            for match in reversed(matches):
                start, end = match.span()
                before = result[:start]
                after = result[end:]

                if before.endswith('$') or after.startswith('$'):
                    continue

                formula = match.group(0)

                if not formula.startswith('$'):
                    formula = '$' + formula + '$'

                result = before + formula + after

        result = re.sub(r'\$([^$]+)\$\s*\$([^$]+)\$', r'$\1 \2$', result)

        return result

    @classmethod
    def process_file(cls, input_path: str, output_path: str = None) -> dict:
        if output_path is None:
            output_path = str(Path(input_path).with_name(
                Path(input_path).stem + '-formatted.md'
            ))

        with open(input_path, 'r', encoding='utf-8') as f:
            content = f.read()

        lines = content.split('\n')
        processed_lines = []
        has_math = False

        for line in lines:
            if line.strip():
                processed = cls.format_formulas(line)
                if processed != line:
                    has_math = True
                processed_lines.append(processed)
            else:
                processed_lines.append(line)

        processed_content = '\n'.join(processed_lines)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(processed_content)

        return {
            'success': True,
            'input_path': input_path,
            'output_path': output_path,
            'has_math': has_math
        }


class MarkdownConverter:
    def __init__(self):
        self.pandoc_available = self._check_pandoc()

    @staticmethod
    def _check_pandoc() -> bool:
        try:
            result = subprocess.run(
                ['pandoc', '--version'],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    @staticmethod
    def _is_markdown(file_path: str) -> bool:
        ext = Path(file_path).suffix.lower()
        if ext in ['.md', '.markdown', '.mdown', '.mkd', '.mkdn']:
            return True

        if ext == '.txt':
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read(5000)

                md_indicators = [
                    r'^#{1,6}\s+',  # 标题
                    r'^\*{1,2}.*?\*{1,2}',  # 强调
                    r'^\d+\.\s+',  # 有序列表
                    r'^[-*+]\s+',  # 无序列表
                    r'^\|.*\|',  # 表格
                    r'^```',  # 代码块
                    r'^\[[\w\s]+\]',  # 链接
                    r'\$\$.*?\$\$',  # 数学公式
                    r'\$.*?\$',  # 行内公式
                ]

                lines = content.split('\n')
                md_score = 0
                for line in lines[:50]:
                    for pattern in md_indicators:
                        if re.match(pattern, line.strip()):
                            md_score += 1
                            break

                return md_score >= 3
            except Exception:
                pass

        return False

    def _convert_with_pandoc(self, input_path: str, output_path: str) -> dict:
        # 注意：不使用 --toc 参数，因为 zero_format_normalizer 会生成目录
        # 避免生成双重目录
        cmd = [
            'pandoc',
            input_path,
            '-o', output_path,
            '-f', 'markdown+tex_math_dollars+tex_math_single_backslash',
            '-t', 'docx+native_numbering',
            '--mathml',
            '--standalone',
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120
            )

            if result.returncode == 0:
                return {
                    'success': True,
                    'output_path': output_path,
                    'method': 'pandoc',
                    'file_size': os.path.getsize(output_path)
                }
            else:
                return {
                    'success': False,
                    'method': 'pandoc',
                    'error': result.stderr or result.stdout
                }
        except Exception as e:
            return {
                'success': False,
                'method': 'pandoc',
                'error': str(e)
            }

    def _preprocess_math(self, input_path: str) -> str:
        temp_dir = Path('workspace/temp')
        temp_dir.mkdir(parents=True, exist_ok=True)
        temp_path = temp_dir / f'preprocessed_{Path(input_path).name}'

        result = MathFormulaProcessor.process_file(input_path, str(temp_path))

        if result['success'] and result['has_math']:
            return str(temp_path)
        return input_path

    def convert(self, input_path: str, output_path: str = None, template_config: dict = None) -> dict:
        if not os.path.exists(input_path):
            return {
                'success': False,
                'error': f'Input file not found: {input_path}'
            }

        if not self._is_markdown(input_path):
            return {
                'success': False,
                'error': f'File is not a Markdown file: {input_path}'
            }

        if not self.pandoc_available:
            return {
                'success': False,
                'error': 'pandoc is not installed. Install with: winget install JohnMacFarlane.Pandoc'
            }

        if output_path is None:
            output_path = str(Path(input_path).with_suffix('.docx'))

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        processed_path = self._preprocess_math(input_path)

        result = self._convert_with_pandoc(processed_path, output_path)

        if processed_path != input_path:
            Path(processed_path).unlink(missing_ok=True)

        if result['success']:
            result['input_path'] = input_path
            print(f"[INFO] Markdown converted to DOCX: {output_path}")

        return result

    def run(self, input_path: str, output_path: str = None) -> dict:
        return self.convert(input_path, output_path)


def main():
    if len(sys.argv) < 2:
        print("Usage: python md_converter.py <input_file> [output_file]")
        sys.exit(1)

    input_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else None

    converter = MarkdownConverter()
    result = converter.convert(input_path, output_path)

    print(json.dumps(result, indent=2, ensure_ascii=False))

    if not result['success']:
        sys.exit(1)


if __name__ == '__main__':
    main()
