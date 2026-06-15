#!/usr/bin/env python3
"""
Document Converter - 统一文档格式转换器
支持：DOCX ↔ MD、PDF/PPTX/XLSX/HTML → MD → DOCX
"""

import os
import re
import sys
import json
import shutil
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional, List
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


# ============================================================
# 数学公式处理（原 markdown-converter）
# ============================================================

class MathFormulaProcessor:
    """LaTeX 数学公式检测与格式化"""
    
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
            output_path = str(Path(input_path).with_name(Path(input_path).stem + '-formatted.md'))

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

        return {'success': True, 'input_path': input_path, 'output_path': output_path, 'has_math': has_math}


# ============================================================
# Pandoc 转换器（原 markdown-converter）
# ============================================================

class PandocConverter:
    """使用 pandoc 将 Markdown 转换为 DOCX"""
    
    def __init__(self):
        self.pandoc_available = self._check_pandoc()

    @staticmethod
    def _check_pandoc() -> bool:
        try:
            result = subprocess.run(['pandoc', '--version'], capture_output=True, text=True, timeout=10)
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def convert_md_to_docx(self, input_path: str, output_path: str = None) -> dict:
        """将 Markdown 转换为 DOCX"""
        if not self.pandoc_available:
            return {'success': False, 'error': 'pandoc 未安装。安装命令: winget install JohnMacFarlane.Pandoc'}

        if output_path is None:
            output_path = str(Path(input_path).with_suffix('.docx'))

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        # 预处理数学公式
        temp_dir = Path('workspace/temp')
        temp_dir.mkdir(parents=True, exist_ok=True)
        temp_path = temp_dir / f'preprocessed_{Path(input_path).name}'
        
        result = MathFormulaProcessor.process_file(input_path, str(temp_path))
        processed_path = str(temp_path) if result['success'] and result['has_math'] else input_path

        # 使用 pandoc 转换
        cmd = [
            'pandoc', processed_path, '-o', output_path,
            '-f', 'markdown+tex_math_dollars+tex_math_single_backslash',
            '-t', 'docx+native_numbering',
            '--mathml', '--standalone',
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            
            # 清理临时文件
            if processed_path != input_path:
                Path(processed_path).unlink(missing_ok=True)

            if result.returncode == 0:
                return {'success': True, 'output_path': output_path, 'method': 'pandoc', 'file_size': os.path.getsize(output_path)}
            else:
                return {'success': False, 'method': 'pandoc', 'error': result.stderr or result.stdout}
        except Exception as e:
            return {'success': False, 'method': 'pandoc', 'error': str(e)}


# ============================================================
# MarkItDown 转换器
# ============================================================

class MarkItDownConverter:
    """
    统一文档转换器
    - DOCX/PDF/PPTX/XLSX/HTML → Markdown（使用 markitdown）
    - Markdown → DOCX（使用 pandoc）
    """
    
    def __init__(self, enable_plugins: bool = False, **kwargs):
        self.enable_plugins = enable_plugins
        self.kwargs = kwargs
        self._markitdown = None
        self._pandoc_converter = None
        
    def _get_markitdown(self):
        """延迟加载 MarkItDown 实例"""
        if self._markitdown is None:
            try:
                from markitdown import MarkItDown
                self._markitdown = MarkItDown(enable_plugins=self.enable_plugins, **self.kwargs)
                logger.info("MarkItDown 实例初始化成功")
            except ImportError as e:
                logger.error(f"无法导入 markitdown 库: {e}")
                logger.error("请安装 markitdown: pip install 'markitdown[all]'")
                raise
        return self._markitdown
    
    def _get_pandoc_converter(self):
        """延迟加载 PandocConverter 实例"""
        if self._pandoc_converter is None:
            self._pandoc_converter = PandocConverter()
        return self._pandoc_converter
    
    def _is_markdown(self, file_path: str) -> bool:
        """检测文件是否为 Markdown 格式"""
        ext = Path(file_path).suffix.lower()
        if ext in ['.md', '.markdown', '.mdown', '.mkd', '.mkdn']:
            return True
        if ext == '.txt':
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read(5000)
                md_indicators = [
                    r'^#{1,6}\s+', r'^\*{1,2}.*?\*{1,2}', r'^\d+\.\s+',
                    r'^[-*+]\s+', r'^\|.*\|', r'^```', r'^\[[\w\s]+\]',
                    r'\$\$.*?\$\$', r'\$.*?\$',
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
    
    def convert(self, input_path: str, output_path: Optional[str] = None) -> Dict[str, Any]:
        """
        智能转换文档：
        - MD/TXT → DOCX（使用 pandoc）
        - DOCX/PDF/PPTX/XLSX/HTML → MD（使用 markitdown）
        """
        try:
            input_path = Path(input_path)
            if not input_path.exists():
                return {'success': False, 'error': f'输入文件不存在: {input_path}', 'input_path': str(input_path)}
            
            logger.info(f"开始转换文件: {input_path}")
            
            # 判断输入格式
            if self._is_markdown(str(input_path)):
                # MD → DOCX
                pandoc = self._get_pandoc_converter()
                if output_path is None:
                    output_path = str(input_path.with_suffix('.docx'))
                return pandoc.convert_md_to_docx(str(input_path), output_path)
            else:
                # 其他格式 → MD
                md = self._get_markitdown()
                result = md.convert(str(input_path))
                content = result.text_content
                
                if output_path:
                    output_path = Path(output_path)
                    output_path.parent.mkdir(parents=True, exist_ok=True)
                    with open(output_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    logger.info(f"Markdown 已保存到: {output_path}")
                
                metadata = self._extract_metadata(content)
                
                return {
                    'success': True,
                    'input_path': str(input_path),
                    'output_path': str(output_path) if output_path else None,
                    'content': content,
                    'metadata': metadata,
                    'file_size': input_path.stat().st_size
                }
            
        except Exception as e:
            logger.error(f"转换失败: {e}")
            return {'success': False, 'error': str(e), 'input_path': str(input_path)}
    
    def convert_to_docx(self, input_path: str, output_path: str = None) -> Dict[str, Any]:
        """
        将任意格式转换为 DOCX：
        - MD → DOCX（直接转换）
        - 其他格式 → MD → DOCX（两步转换）
        """
        input_path = Path(input_path)
        
        if self._is_markdown(str(input_path)):
            # MD → DOCX
            pandoc = self._get_pandoc_converter()
            if output_path is None:
                output_path = str(input_path.with_suffix('.docx'))
            return pandoc.convert_md_to_docx(str(input_path), output_path)
        else:
            # 其他格式 → MD → DOCX
            temp_md = str(input_path.with_suffix('.md'))
            md_result = self.convert(str(input_path), temp_md)
            
            if not md_result['success']:
                return md_result
            
            pandoc = self._get_pandoc_converter()
            if output_path is None:
                output_path = str(input_path.with_suffix('.docx'))
            
            result = pandoc.convert_md_to_docx(temp_md, output_path)
            
            # 清理临时 MD 文件
            if os.path.exists(temp_md):
                os.remove(temp_md)
            
            return result
    
    def extract_text(self, input_path: str) -> Dict[str, Any]:
        """提取纯文本内容"""
        try:
            result = self.convert(input_path)
            if result['success']:
                content = result.get('content', '')
                return {'success': True, 'text_content': content, 'word_count': len(content.split()), 'input_path': result['input_path']}
            return result
        except Exception as e:
            return {'success': False, 'error': str(e), 'input_path': str(input_path)}
    
    def get_metadata(self, input_path: str) -> Dict[str, Any]:
        """获取文档元数据"""
        try:
            result = self.convert(input_path)
            if result['success']:
                return {'success': True, 'metadata': result.get('metadata', {}), 'input_path': result['input_path']}
            return result
        except Exception as e:
            return {'success': False, 'error': str(e), 'input_path': str(input_path)}
    
    def _extract_metadata(self, content: str) -> Dict[str, Any]:
        """从内容中提取元数据"""
        metadata = {}
        lines = content.split('\n')
        
        for line in lines:
            if line.startswith('# '):
                metadata['title'] = line[2:].strip()
                break
        
        metadata['word_count'] = len(content.split())
        metadata['line_count'] = len(lines)
        metadata['table_count'] = content.count('| --- |')
        metadata['image_count'] = content.count('![')
        metadata['link_count'] = max(0, content.count('[') - metadata['image_count'])
        
        return metadata
    
    def batch_convert(self, input_dir: str, output_dir: str, extensions: Optional[List[str]] = None) -> Dict[str, Any]:
        """批量转换目录中的文件"""
        try:
            input_dir = Path(input_dir)
            output_dir = Path(output_dir)
            
            if not input_dir.exists():
                return {'success': False, 'error': f'输入目录不存在: {input_dir}'}
            
            if extensions is None:
                extensions = ['.docx', '.pdf', '.pptx', '.xlsx', '.html', '.htm']
            
            output_dir.mkdir(parents=True, exist_ok=True)
            results = []
            success_count = 0
            error_count = 0
            
            for file_path in input_dir.iterdir():
                if file_path.is_file() and file_path.suffix.lower() in extensions:
                    output_path = output_dir / f"{file_path.stem}.md"
                    result = self.convert(str(file_path), str(output_path))
                    results.append({
                        'input': str(file_path),
                        'output': str(output_path),
                        'success': result['success'],
                        'error': result.get('error')
                    })
                    if result['success']:
                        success_count += 1
                    else:
                        error_count += 1
            
            return {'success': True, 'total_files': len(results), 'success_count': success_count, 'error_count': error_count, 'results': results}
        except Exception as e:
            return {'success': False, 'error': str(e)}


def main():
    """命令行入口"""
    if len(sys.argv) < 2:
        print("用法:")
        print("  python markitdown_converter.py <input_file> [output_file]")
        print("")
        print("示例:")
        print("  python markitdown_converter.py document.docx output.md    # DOCX → MD")
        print("  python markitdown_converter.py document.md output.docx    # MD → DOCX")
        print("  python markitdown_converter.py document.pdf output.md     # PDF → MD")
        print("  python markitdown_converter.py document.pdf output.docx   # PDF → DOCX")
        sys.exit(1)
    
    input_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else None
    
    converter = MarkItDownConverter()
    
    # 根据输出格式判断使用哪种转换
    if output_path and output_path.endswith('.docx'):
        result = converter.convert_to_docx(input_path, output_path)
    else:
        result = converter.convert(input_path, output_path)
    
    if result['success']:
        print(f"转换成功!")
        print(f"输入文件: {result.get('input_path', input_path)}")
        if result.get('output_path'):
            print(f"输出文件: {result['output_path']}")
        if 'file_size' in result:
            print(f"文件大小: {result['file_size']} 字节")
        if 'metadata' in result:
            print("\n文档元数据:")
            for key, value in result['metadata'].items():
                print(f"  {key}: {value}")
        if not output_path and 'content' in result:
            print("\n内容预览 (前 500 字符):")
            print("-" * 50)
            print(result['content'][:500])
            if len(result['content']) > 500:
                print("...")
    else:
        print(f"转换失败: {result['error']}")
        sys.exit(1)


if __name__ == '__main__':
    main()