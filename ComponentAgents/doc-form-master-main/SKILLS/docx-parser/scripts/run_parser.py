import sys
import os

script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, "..", "..", ".."))

sys.path.insert(0, script_dir)

from parser import DocxParser

docx_path = os.path.join(project_root, "workspace", "input", "2029年中国AI与数据要素双轮驱动下的数据科学与大数据技术专业人才竞争力与学业研判报告.docx")
output_path = os.path.join(project_root, "workspace", "parsed", "document_ast.json")

parser = DocxParser(docx_path)
parser.export_ast.__code__  
parser.ast = parser.ast  

parser.validate_docx()
parser.parse_metadata()
parser.parse_styles()
parser.parse_paragraphs()
parser.parse_tables()
parser.extract_images()
parser.parse_formulas()
parser._identify_sections()
parser.export_ast(output_path)

print("[INFO] AST exported successfully to:", output_path)
