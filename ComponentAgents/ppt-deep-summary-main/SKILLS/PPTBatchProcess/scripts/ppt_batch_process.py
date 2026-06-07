"""
批量处理多个PPT文件
支持一次处理多个PPT文件，为每个文件生成独立的分析结果
"""

import json
import sys
from pathlib import Path
from typing import Any
from datetime import datetime

# 添加scripts目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "PPTParser" / "scripts"))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "PPTAnalyst" / "scripts"))

from ppt_parser import parse, to_json as parser_to_json
from ppt_analyst import analyze, to_json as analyst_to_json


def process_single_file(pptx_path: Path, output_dir: Path) -> dict[str, Any]:
    """处理单个PPT文件"""
    file_stem = pptx_path.stem
    work_dir = output_dir / file_stem
    work_dir.mkdir(parents=True, exist_ok=True)
    
    # 初始化结果结构（与 AGENT.md 的 manifest.json 结构一致）
    result = {
        "source_file": pptx_path.name,
        "status": "failed",
        "output_dir": str(work_dir),
        "parsed_json": str(work_dir / "parsed.json"),
        "parsed_md": str(work_dir / "parsed.md"),
        "outline_json": str(work_dir / "outline.json"),
        "slide_count": 0,
        "main_topic": "",
        "key_themes": [],
        "warnings": [],
        "error": None
    }
    
    try:
        # Step 1: 解析PPT
        parsed_json = work_dir / "parsed.json"
        parsed_md = work_dir / "parsed.md"
        parsed_result = parse(pptx_path, json_output=parsed_json, md_output=parsed_md)
        
        result["slide_count"] = parsed_result.slide_count
        result["warnings"] = parsed_result.warnings
        
        # Step 2: 内容分析
        outline_json = work_dir / "outline.json"
        
        # 读取解析结果的JSON数据
        with open(parsed_json, 'r', encoding='utf-8') as f:
            parsed_data = json.load(f)
        
        # 分析内容
        analysis_result = analyze(parsed_data)
        
        # 保存分析结果
        with open(outline_json, 'w', encoding='utf-8') as f:
            f.write(analyst_to_json(analysis_result))
        
        result["main_topic"] = analysis_result.presentation_overview.main_topic
        result["key_themes"] = analysis_result.presentation_overview.key_themes
        result["status"] = "success"
        
    except Exception as e:
        result["error"] = str(e)
    
    return result


def batch_process(input_path: str | Path, output_dir: str | Path = None) -> list[dict[str, Any]]:
    """
    批量处理PPT文件
    
    Args:
        input_path: 可以是：
            - 单个PPT文件路径
            - 包含PPT文件的目录路径
            - PPT文件路径列表
        output_dir: 输出目录，默认为输入路径下的 batch_output 目录
    
    Returns:
        处理结果列表
    """
    input_path = Path(input_path)
    
    # 确定输出目录
    if output_dir is None:
        if input_path.is_dir():
            output_dir = input_path / "batch_output"
        else:
            output_dir = input_path.parent / "batch_output"
    else:
        output_dir = Path(output_dir)
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 收集所有PPT文件
    pptx_files = []
    
    if isinstance(input_path, (list, tuple)):
        # 输入是文件列表
        pptx_files = [Path(f) for f in input_path]
    elif input_path.is_file():
        # 输入是单个文件
        pptx_files = [input_path]
    elif input_path.is_dir():
        # 输入是目录，跳过临时文件（~$ 开头）
        pptx_files = sorted([f for f in input_path.glob("*.pptx") if not f.name.startswith('~$')])
    else:
        raise ValueError(f"无效的输入路径: {input_path}")
    
    if not pptx_files:
        print(f"未找到PPT文件: {input_path}")
        return []
    
    print(f"找到 {len(pptx_files)} 个PPT文件")
    print(f"输出目录: {output_dir}")
    print("=" * 60)
    
    # 处理每个文件
    results = []
    for i, pptx_file in enumerate(pptx_files, 1):
        print(f"\n[{i}/{len(pptx_files)}] 处理: {pptx_file.name}")
        result = process_single_file(pptx_file, output_dir)
        results.append(result)
        
        if result["status"] == "success":
            print(f"  ✓ 成功 - {result['main_topic']}")
            print(f"    幻灯片数: {result['slide_count']}")
            print(f"    关键主题: {result['key_themes']}")
        else:
            print(f"  ✗ 失败 - {result['error']}")
    
    # 汇总
    success_count = sum(1 for r in results if r["status"] == "success")
    failed_count = sum(1 for r in results if r["status"] == "failed")
    
    print("\n" + "=" * 60)
    print("处理完成")
    print(f"成功: {success_count}/{len(results)}")
    print(f"失败: {failed_count}/{len(results)}")
    
    # 生成 manifest.json（与 AGENT.md 结构一致）
    manifest = {
        "status": "completed" if failed_count == 0 else "partial",
        "total_files": len(results),
        "success_count": success_count,
        "failed_count": failed_count,
        "documents": results,
        "has_combined_summary": len(results) > 1,
        "combined_summary_json": str(output_dir / "综合总结.json") if len(results) > 1 else None,
        "combined_summary_md": str(output_dir / "综合总结.md") if len(results) > 1 else None,
        "generated_at": datetime.now().isoformat()
    }
    
    manifest_file = output_dir / "manifest.json"
    with open(manifest_file, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    
    print(f"\n处理清单: {manifest_file}")
    
    return results


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="批量处理PPT文件")
    parser.add_argument("input", help="PPT文件路径、目录路径或多个文件路径（用逗号分隔）")
    parser.add_argument("-o", "--output", help="输出目录", default=None)
    
    args = parser.parse_args()
    
    # 处理多个文件的情况
    input_path = args.input
    if "," in input_path:
        input_path = [p.strip() for p in input_path.split(",")]
    
    try:
        results = batch_process(input_path, args.output)
        
        # 返回成功/失败状态
        if all(r["status"] == "success" for r in results):
            sys.exit(0)
        else:
            sys.exit(1)
            
    except Exception as e:
        print(f"错误: {e}")
        sys.exit(1)
