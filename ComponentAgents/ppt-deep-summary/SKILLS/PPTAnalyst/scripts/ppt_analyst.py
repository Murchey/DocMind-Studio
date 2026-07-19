import json
import re
from pathlib import Path
from typing import Any
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class KeyPoint:
    point: str = ""
    supporting_data: str = ""
    source_slide: int = 0
    confidence: str = "high"


@dataclass
class Section:
    section_id: int = 0
    title: str = ""
    key_points: list[KeyPoint] = field(default_factory=list)
    sub_sections: list["Section"] = field(default_factory=list)


@dataclass
class PresentationOverview:
    title: str = ""
    total_slides: int = 0
    main_topic: str = ""
    key_themes: list[str] = field(default_factory=list)


@dataclass
class Insights:
    strengths: list[str] = field(default_factory=list)
    gaps: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)


@dataclass
class AnalysisMetadata:
    analysis_timestamp: str = ""
    requires_user_review: bool = True


@dataclass
class AnalysisResult:
    presentation_overview: PresentationOverview = field(default_factory=PresentationOverview)
    outline: list[Section] = field(default_factory=list)
    insights: Insights = field(default_factory=Insights)
    metadata: AnalysisMetadata = field(default_factory=AnalysisMetadata)
    warnings: list[str] = field(default_factory=list)


class PPTAnalystError(Exception):
    pass


def validate_input(data: dict[str, Any]) -> None:
    if not data or "slides" not in data or not isinstance(data["slides"], list):
        raise PPTAnalystError("输入数据无效，缺少 slides 数组")


def extract_overview(data: dict[str, Any]) -> PresentationOverview:
    themes = [s.get("title", "") for s in data.get("slides", []) if s.get("title")]
    return PresentationOverview(title=data.get("presentation_title", "未知"), total_slides=data.get("slide_count", 0),
                                main_topic=themes[0] if themes else "未知主题", key_themes=themes)


def summarize_slide_content(slide: dict[str, Any]) -> str:
    num = slide.get("slide_number", 0)
    title = slide.get("title", "")
    texts = [t.get("text", "") for t in slide.get("texts", []) if t.get("text", "")]
    tables = slide.get("tables", [])
    charts = slide.get("charts", [])
    notes = slide.get("notes", [])
    images = slide.get("images", [])

    summary_parts = []

    if title:
        summary_parts.append(f"主题：{title}")

    if texts:
        summary_parts.append(f"包含 {len(texts)} 条文本内容")

    if tables:
        total_rows = sum(t.get("row_count", 0) for t in tables)
        total_cols = sum(t.get("col_count", 0) for t in tables)
        summary_parts.append(f"包含 {len(tables)} 个表格（共 {total_rows} 行 × {total_cols} 列）")

    if charts:
        chart_types = [c.get("chart_type", "未知") for c in charts]
        summary_parts.append(f"包含 {len(charts)} 个图表（类型：{', '.join(chart_types)}）")

    if notes:
        summary_parts.append(f"包含 {len(notes)} 条备注说明")

    if images:
        summary_parts.append(f"包含 {len(images)} 张图片")

    if not summary_parts:
        return f"Slide {num} 内容较少"

    return f"Slide {num}：{'；'.join(summary_parts)}"


SECTION_PATTERN = re.compile(r"^(\d{2})\s+(.+)")

_TEXT_MIN_LEN = 8
_TEXT_MAX_PER_SLIDE = 8


def _truncate(text: str, max_len: int = 120) -> str:
    return text if len(text) <= max_len else text[:max_len - 1] + "…"


def _detect_section_title(slide: dict[str, Any]) -> str | None:
    title = slide.get("title", "")
    if title and SECTION_PATTERN.match(title):
        return title
    for t in slide.get("texts", []):
        txt = t.get("text", "").strip()
        if txt and SECTION_PATTERN.match(txt):
            return txt
    return None


def extract_key_points(slide: dict[str, Any]) -> list[KeyPoint]:
    points: list[KeyPoint] = []
    num = slide.get("slide_number", 0)
    title = slide.get("title", "")

    if title:
        points.append(KeyPoint(point=title, supporting_data=f"Slide {num} 标题", source_slide=num, confidence="high"))

    texts = [t.get("text", "") for t in slide.get("texts", []) if t.get("text", "") and len(t.get("text", "")) >= _TEXT_MIN_LEN]
    for text in texts[:_TEXT_MAX_PER_SLIDE]:
        points.append(KeyPoint(point=_truncate(text), supporting_data=f"Slide {num} 文本", source_slide=num, confidence="high"))

    tables = slide.get("tables", [])
    if tables:
        total_rows = sum(t.get("row_count", 0) for t in tables)
        total_cols = sum(t.get("col_count", 0) for t in tables)
        points.append(KeyPoint(point=f"包含 {len(tables)} 个数据表格（共 {total_rows} 行 × {total_cols} 列）", supporting_data=f"Slide {num} 表格数据", source_slide=num, confidence="high"))

    charts = slide.get("charts", [])
    if charts:
        chart_info = "、".join([f"{c.get('chart_type', '未知')}图表" for c in charts[:2]])
        points.append(KeyPoint(point=f"包含 {len(charts)} 个图表：{chart_info}", supporting_data=f"Slide {num} 可视化数据", source_slide=num, confidence="medium"))

    notes = slide.get("notes", [])
    if notes:
        key_notes = [n for n in notes if len(n) > 10][:2]
        for note in key_notes:
            points.append(KeyPoint(point=_truncate(note), supporting_data=f"Slide {num} 演讲备注", source_slide=num, confidence="medium"))

    return points


def build_outline(data: dict[str, Any]) -> list[Section]:
    sections: list[Section] = []
    slides = data.get("slides", [])
    if not slides:
        return sections

    section_id = 0
    current_section: Section | None = None

    for i, slide in enumerate(slides):
        num = slide.get("slide_number", i + 1)
        title = slide.get("title", "")
        points = extract_key_points(slide)
        section_title = _detect_section_title(slide)

        if section_title:
            if current_section and current_section.title == section_title:
                current_section.key_points.extend(points)
            else:
                if current_section is not None and (current_section.key_points or current_section.sub_sections):
                    sections.append(current_section)
                    section_id += 1
                filtered = [p for p in points if p.point != section_title]
                current_section = Section(section_id=section_id, title=section_title, key_points=filtered)
        elif current_section is None:
            section_id += 1
            current_section = Section(section_id=section_id, title=title or "整体概述", key_points=points)
        else:
            sub = Section(section_id=section_id, title=f"Slide {num}" + (f" — {title}" if title else ""), key_points=points)
            current_section.sub_sections.append(sub)

    if current_section is not None and (current_section.key_points or current_section.sub_sections):
        sections.append(current_section)

    return sections


def analyze_insights(data: dict[str, Any], sections: list[Section]) -> Insights:
    slides = data.get("slides", [])
    warnings = data.get("warnings", [])
    insights = Insights()

    if warnings:
        insights.gaps.append(f"有 {len(warnings)} 页解析失败")
    if any(s.get("tables") for s in slides):
        insights.strengths.append("包含结构化表格数据")
    if any(s.get("charts") for s in slides):
        insights.strengths.append("包含可视化图表")
    if any(s.get("notes") for s in slides):
        insights.strengths.append("包含演讲备注")
    if sum(len(s.key_points) for s in sections) < 5:
        insights.gaps.append("内容要点较少")
    if not any(s.get("tables") for s in slides) and not any(s.get("charts") for s in slides):
        insights.recommendations.append("建议添加数据图表")
    return insights


def check_warnings(data: dict[str, Any]) -> list[str]:
    warnings = list(data.get("warnings", []))
    for slide in data.get("slides", []):
        if not any([slide.get("texts"), slide.get("tables"), slide.get("charts")]):
            warnings.append(f"Slide {slide.get('slide_number', 0)} 内容为空")
    return warnings


def analyze(data: dict[str, Any]) -> AnalysisResult:
    validate_input(data)
    outline = build_outline(data)
    return AnalysisResult(presentation_overview=extract_overview(data), outline=outline,
                          insights=analyze_insights(data, outline), warnings=check_warnings(data),
                          metadata=AnalysisMetadata(analysis_timestamp=datetime.now().isoformat(), requires_user_review=True))


def to_dict(result: AnalysisResult) -> dict[str, Any]:
    def sec_dict(s: Section) -> dict[str, Any]:
        return {"section_id": s.section_id, "title": s.title,
                "key_points": [{"point": p.point, "supporting_data": p.supporting_data, "source_slide": p.source_slide, "confidence": p.confidence} for p in s.key_points],
                "sub_sections": [sec_dict(sub) for sub in s.sub_sections]}

    return {
        "presentation_overview": {"title": result.presentation_overview.title, "total_slides": result.presentation_overview.total_slides,
                                  "main_topic": result.presentation_overview.main_topic, "key_themes": result.presentation_overview.key_themes},
        "outline": {"sections": [sec_dict(s) for s in result.outline]},
        "insights": {"strengths": result.insights.strengths, "gaps": result.insights.gaps, "recommendations": result.insights.recommendations},
        "metadata": {"analysis_timestamp": result.metadata.analysis_timestamp, "requires_user_review": result.metadata.requires_user_review},
        "warnings": result.warnings
    }


def to_json(result: AnalysisResult, indent: int = 2) -> str:
    return json.dumps(to_dict(result), ensure_ascii=False, indent=indent)


def analyze_from_file(input_path: str | Path, output_path: str | Path | None = None) -> AnalysisResult:
    input_path = Path(input_path)
    if not input_path.exists():
        raise PPTAnalystError(f"文件不存在: {input_path}")
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    result = analyze(data)
    if output_path:
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        Path(output_path).write_text(to_json(result), encoding='utf-8')
    return result


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("用法: python ppt_analyst.py <parsed.json> [output.json]")
        sys.exit(1)
    try:
        result = analyze_from_file(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
        print(to_json(result))
    except PPTAnalystError as e:
        print(json.dumps({"status": "error", "reason": str(e)}))
        sys.exit(1)
