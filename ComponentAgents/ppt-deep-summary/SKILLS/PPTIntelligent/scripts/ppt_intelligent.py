"""
PPT 智能分析 — 上下文准备脚本

本脚本为 AI 原生的 PPTIntelligent Skill 提供数据准备服务。
AI 助手直接执行智能分析（语义分析、逻辑分析、智能总结），
本脚本仅负责：读取 parsed.json → 生成结构化的纯文本上下文（供 AI 阅读）。

使用方式：
  python ppt_intelligent.py <parsed.json> [context.txt]

输出：
  - context.txt：纯文本格式的 PPT 内容摘要（供 AI 分析使用）
  - 或标准输出
"""

import json
import sys
from pathlib import Path
from datetime import datetime


def extract_context(parsed_data: dict) -> str:
    """从 parsed.json 提取结构化的纯文本上下文"""
    lines = []
    lines.append(f"# PPT 分析上下文")
    lines.append(f"生成时间: {datetime.now().isoformat()}")
    lines.append(f"总页数: {parsed_data.get('slide_count', 0)}")
    lines.append(f"标题: {parsed_data.get('presentation_title', '未知')}")
    lines.append("")

    slides = parsed_data.get("slides", [])
    for slide in slides:
        num = slide.get("slide_number", 0)
        title = slide.get("title", "")
        lines.append(f"--- Slide {num} ---")
        if title:
            lines.append(f"标题: {title}")
        if slide.get("layout_name"):
            lines.append(f"布局: {slide['layout_name']}")

        texts = [t.get("text", "") for t in slide.get("texts", []) if t.get("text")]
        for t in texts:
            lines.append(f"  {t}")

        if slide.get("notes"):
            for n in slide["notes"]:
                lines.append(f"  [备注] {n}")

        tables = slide.get("tables", [])
        if tables:
            lines.append(f"  [表格] {len(tables)} 个")
            for i, tbl in enumerate(tables[:2]):
                rows = tbl.get("rows", [])
                if rows:
                    lines.append(f"    表{i+1}: {len(rows)}行 x {tbl.get('col_count', 0)}列")
                    lines.append(f"    表头: {' | '.join(rows[0])}")

        images = slide.get("images", [])
        if images:
            lines.append(f"  [图片] {len(images)} 张")
            for img in images:
                desc = f"    文件名: {img.get('filename','?')}"
                if img.get("width") and img.get("height"):
                    desc += f" ({img['width']:.1f}x{img['height']:.1f} inches)"
                lines.append(desc)

        charts = slide.get("charts", [])
        if charts:
            for c in charts:
                chart_desc = f"  [图表] 类型: {c.get('chart_type','?')}"
                if c.get("title"):
                    chart_desc += f", 标题: {c['title']}"
                lines.append(chart_desc)

        hyperlinks = slide.get("hyperlinks", [])
        if hyperlinks:
            for h in hyperlinks[:3]:
                lines.append(f"  [链接] {h.get('text','?')} -> {h.get('url','?')}")

        lines.append("")

    if parsed_data.get("warnings"):
        lines.append("--- 警告 ---")
        for w in parsed_data["warnings"]:
            lines.append(f"  ⚠ {w}")

    return "\n".join(lines)


def main():
    if len(sys.argv) < 2:
        print("用法: python ppt_intelligent.py <parsed.json> [context.txt]")
        sys.exit(1)

    input_path = Path(sys.argv[1])
    if not input_path.exists():
        print(json.dumps({"status": "error", "reason": f"文件不存在: {input_path}"}))
        sys.exit(1)

    with open(input_path, 'r', encoding='utf-8') as f:
        parsed_data = json.load(f)

    context = extract_context(parsed_data)

    if len(sys.argv) > 2:
        output_path = Path(sys.argv[2])
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(context, encoding='utf-8')
        print(f"上下文已写入: {output_path}")
    else:
        print(context)


if __name__ == "__main__":
    main()
