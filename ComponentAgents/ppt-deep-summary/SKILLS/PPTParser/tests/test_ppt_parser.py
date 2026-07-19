"""
PPTParser 测试脚本
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from ppt_parser import parse, to_json, to_markdown, PPTParserError


def test_ppt_parser():
    test_file = Path(__file__).parent.parent.parent.parent / "test.pptx"

    if not test_file.exists():
        print(f"[SKIP] 测试文件不存在: {test_file}")
        return False

    print(f"[INFO] 测试文件: {test_file}")
    print("=" * 60)

    try:
        result = parse(test_file)

        print(f"\n[SUCCESS] 解析成功!")
        print(f"  - 演示文稿标题: {result.presentation_title}")
        print(f"  - 幻灯片数量: {result.slide_count}")
        print(f"  - 警告数量: {len(result.warnings)}")

        if result.warnings:
            print("\n[WARNINGS]")
            for w in result.warnings:
                print(f"  - {w}")

        print("\n" + "=" * 60)
        print("[DETAIL] 各幻灯片详情:")
        print("=" * 60)

        for slide in result.slides:
            print(f"\n--- Slide {slide.slide_number} ---")
            print(f"  布局: {slide.layout_name or 'N/A'}")
            print(f"  标题: {slide.title or 'N/A'}")
            print(f"  文本项数量: {len(slide.texts)}")
            print(f"  备注数量: {len(slide.notes)}")
            print(f"  表格数量: {len(slide.tables)}")
            print(f"  图片数量: {len(slide.images)}")
            print(f"  超链接数量: {len(slide.hyperlinks)}")
            print(f"  图表数量: {len(slide.charts)}")

            if slide.texts:
                print("  文本内容:")
                for t in slide.texts[:3]:
                    print(f"    [L{t.level}] {t.text[:50]}...")
                if len(slide.texts) > 3:
                    print(f"    ... 还有 {len(slide.texts) - 3} 项")

            if slide.notes:
                print(f"  备注: {slide.notes[0][:50]}...")

            if slide.tables:
                print(f"  表格: {slide.tables[0].row_count}x{slide.tables[0].col_count}")

            if slide.images:
                print(f"  图片: {slide.images[0].filename}")

            if slide.hyperlinks:
                print(f"  超链接: {slide.hyperlinks[0].url}")

            if slide.charts:
                print(f"  图表类型: {slide.charts[0].chart_type}")

        print("\n" + "=" * 60)
        print("[OUTPUT] JSON 输出预览 (前500字符):")
        print("=" * 60)
        json_str = to_json(result)
        print(json_str[:500] + "..." if len(json_str) > 500 else json_str)

        print("\n" + "=" * 60)
        print("[OUTPUT] Markdown 输出预览 (前500字符):")
        print("=" * 60)
        md_str = to_markdown(result)
        print(md_str[:500] + "..." if len(md_str) > 500 else md_str)

        print("\n" + "=" * 60)
        print("[FILE] 保存测试输出文件...")

        output_dir = Path(__file__).parent / "test_output"
        output_dir.mkdir(exist_ok=True)

        json_output = output_dir / "test_result.json"
        md_output = output_dir / "test_result.md"

        parse(test_file, json_output=json_output, md_output=md_output)

        print(f"  - JSON: {json_output}")
        print(f"  - Markdown: {md_output}")

        print("\n" + "=" * 60)
        print("[PASS] 所有测试通过!")
        return True

    except PPTParserError as e:
        print(f"\n[FAIL] PPTParser 错误: {e}")
        return False
    except Exception as e:
        print(f"\n[FAIL] 未知错误: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_ppt_parser()
    sys.exit(0 if success else 1)
