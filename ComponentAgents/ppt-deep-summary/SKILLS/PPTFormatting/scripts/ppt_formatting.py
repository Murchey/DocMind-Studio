import json
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
class SemanticAnalysis:
    core_concepts: list[str] = field(default_factory=list)
    key_arguments: list[dict[str, Any]] = field(default_factory=list)
    implicit_assumptions: list[str] = field(default_factory=list)


@dataclass
class LogicalAnalysis:
    reasoning_chains: list[dict[str, Any]] = field(default_factory=list)
    cause_effect_relationships: list[dict[str, Any]] = field(default_factory=list)
    hidden_connections: list[str] = field(default_factory=list)


@dataclass
class IntelligentSummary:
    one_sentence_summary: str = ""
    key_insights: list[dict[str, Any]] = field(default_factory=list)
    innovation_highlights: list[str] = field(default_factory=list)
    potential_issues: list[str] = field(default_factory=list)
    overall_assessment: str = ""


@dataclass
class ReportData:
    overview: PresentationOverview = field(default_factory=PresentationOverview)
    sections: list[Section] = field(default_factory=list)
    insights: Insights = field(default_factory=Insights)
    semantic_analysis: SemanticAnalysis = field(default_factory=SemanticAnalysis)
    logical_analysis: LogicalAnalysis = field(default_factory=LogicalAnalysis)
    intelligent_summary: IntelligentSummary = field(default_factory=IntelligentSummary)
    timestamp: str = ""
    warnings: list[str] = field(default_factory=list)


class PPTFormattingError(Exception):
    pass


def validate_input(data: dict[str, Any]) -> None:
    if not data or "presentation_overview" not in data or "outline" not in data:
        raise PPTFormattingError("输入数据缺少必要字段")


def parse_input(data: dict[str, Any]) -> ReportData:
    ov = data.get("presentation_overview", {})
    return ReportData(
        overview=PresentationOverview(title=ov.get("title", "未知"), total_slides=ov.get("total_slides", 0),
                                      main_topic=ov.get("main_topic", "未知"), key_themes=ov.get("key_themes", [])),
        sections=[parse_section(s) for s in data.get("outline", {}).get("sections", [])],
        insights=Insights(**data.get("insights", {})),
        timestamp=data.get("metadata", {}).get("analysis_timestamp", datetime.now().isoformat()),
        warnings=data.get("warnings", []))


def parse_section(d: dict[str, Any]) -> Section:
    return Section(section_id=d.get("section_id", 0), title=d.get("title", ""),
                   key_points=[KeyPoint(**p) for p in d.get("key_points", [])],
                   sub_sections=[parse_section(s) for s in d.get("sub_sections", [])])


def confidence_label(c: str) -> str:
    return {"high": "高", "medium": "中", "low": "低 [待确认]"}.get(c, c)


def fmt_md_point(p: KeyPoint) -> str:
    src = f"(Source: Slide {p.source_slide})" if p.source_slide else ""
    return f"- **{p.point}** {src}"


def fmt_md_section(s: Section, heading: str = "###") -> str:
    lines = [f"{heading} {s.title}", ""]
    for p in s.key_points:
        lines.append(fmt_md_point(p))
    for sub in s.sub_sections:
        sub_text = fmt_md_section(sub, heading="####")
        lines.append("")
        lines.append(sub_text)
    lines.append("")
    return "\n".join(lines)


def format_markdown(r: ReportData) -> str:
    themes = "、".join(r.overview.key_themes[:5]) + ("..." if len(r.overview.key_themes) > 5 else "")
    lines = [f"# {r.overview.title}", "", "## 概览", "",
             f"- 总页数：{r.overview.total_slides}", f"- 核心主题：{r.overview.main_topic}", f"- 关键主题：{themes}", "", "---", "",
             "## 分析大纲", ""] + [fmt_md_section(s) for s in r.sections] + ["---", ""]

    # 智能分析部分
    if r.semantic_analysis.core_concepts or r.semantic_analysis.key_arguments:
        lines.extend(["## 语义分析", ""])
        if r.semantic_analysis.core_concepts:
            lines.extend(["### 核心概念", ""] + [f"- {c}" for c in r.semantic_analysis.core_concepts] + [""])
        if r.semantic_analysis.key_arguments:
            lines.extend(["### 主要论点", ""])
            for arg in r.semantic_analysis.key_arguments:
                slide = arg.get("source_slide", 0)
                src = f"(Source: Slide {slide})" if slide else ""
                lines.append(f"- **{arg.get('argument', '')}** {src}")
                if arg.get("evidence"):
                    lines.append(f"  - 证据：{arg['evidence']}")
            lines.append("")
        if r.semantic_analysis.implicit_assumptions:
            lines.extend(["### 隐含假设", ""] + [f"- {a}" for a in r.semantic_analysis.implicit_assumptions] + [""])

    if r.logical_analysis.reasoning_chains or r.logical_analysis.cause_effect_relationships:
        lines.extend(["## 逻辑分析", ""])
        if r.logical_analysis.reasoning_chains:
            lines.extend(["### 推理链条", ""])
            for chain in r.logical_analysis.reasoning_chains:
                validity = chain.get("logical_validity", "")
                validity_label = {"valid": "有效", "questionable": "存疑", "invalid": "无效"}.get(validity, validity)
                slides = chain.get("source_slides", [])
                src = f"(Slides: {', '.join(map(str, slides))})" if slides else ""
                lines.append(f"- **{chain.get('premise', '')}** → **{chain.get('conclusion', '')}** [{validity_label}] {src}")
            lines.append("")
        if r.logical_analysis.cause_effect_relationships:
            lines.extend(["### 因果关系", ""])
            for rel in r.logical_analysis.cause_effect_relationships:
                confidence = rel.get("confidence", "medium")
                confidence_label = {"high": "高", "medium": "中", "low": "低"}.get(confidence, confidence)
                lines.append(f"- **原因：**{rel.get('cause', '')}")
                lines.append(f"  - **结果：**{rel.get('effect', '')} [置信度：{confidence_label}]")
            lines.append("")
        if r.logical_analysis.hidden_connections:
            lines.extend(["### 隐含联系", ""] + [f"- {c}" for c in r.logical_analysis.hidden_connections] + [""])

    if r.intelligent_summary.one_sentence_summary:
        lines.extend(["## 智能总结", ""])
        lines.extend(["### 一句话总结", "", f"> {r.intelligent_summary.one_sentence_summary}", ""])
        if r.intelligent_summary.key_insights:
            lines.extend(["### 关键洞察", ""])
            for insight in r.intelligent_summary.key_insights:
                sig = insight.get("significance", "medium")
                sig_label = {"high": "高", "medium": "中", "low": "低"}.get(sig, sig)
                slide = insight.get("source_slide", 0)
                src = f"(Source: Slide {slide})" if slide else ""
                lines.append(f"- **{insight.get('insight', '')}** [{sig_label}] {src}")
            lines.append("")
        if r.intelligent_summary.innovation_highlights:
            lines.extend(["### 创新亮点", ""] + [f"- {h}" for h in r.intelligent_summary.innovation_highlights] + [""])
        if r.intelligent_summary.potential_issues:
            lines.extend(["### 潜在问题", ""] + [f"- {i}" for i in r.intelligent_summary.potential_issues] + [""])
        if r.intelligent_summary.overall_assessment:
            lines.extend(["### 整体评价", "", r.intelligent_summary.overall_assessment, ""])

    lines.extend(["---", "", "## 洞察分析", ""])
    if r.insights.strengths:
        lines.extend(["### 内容亮点", ""] + [f"- {s}" for s in r.insights.strengths] + [""])
    if r.insights.gaps:
        lines.extend(["### 信息缺口", ""] + [f"- {g}" for g in r.insights.gaps] + [""])
    if r.insights.recommendations:
        lines.extend(["### 改进建议", ""] + [f"- {rec}" for rec in r.insights.recommendations] + [""])
    if r.warnings:
        lines.extend(["### 警告信息", ""] + [f"- {w}" for w in r.warnings] + [""])

    lines.extend(["---", "", f"*报告生成时间：{r.timestamp}*", "*本报告基于 PPTParser、PPTAnalyst 和 PPTIntelligent 自动生成*"])
    return "\n".join(lines)


def fmt_html_point(p: KeyPoint) -> str:
    src = f'<span class="source">(Source: Slide {p.source_slide})</span>' if p.source_slide else ""
    return f'<div class="key-point"><div class="point-header"><strong>{p.point}</strong> {src}</div></div>'


def fmt_html_section(s: Section, heading: str = "h3") -> str:
    subs_html = "".join(fmt_html_section(sub, heading="h4") for sub in s.sub_sections)
    return f'<div class="section"><{heading}>{s.title}</{heading}>' + "".join(fmt_html_point(p) for p in s.key_points) + subs_html + '</div>'


def format_html(r: ReportData) -> str:
    themes = "、".join(r.overview.key_themes[:5]) + ("..." if len(r.overview.key_themes) > 5 else "")
    sections_html = "".join(fmt_html_section(s) for s in r.sections)
    
    # 智能分析部分
    semantic_html = ""
    if r.semantic_analysis.core_concepts or r.semantic_analysis.key_arguments:
        concepts_html = "<ul>" + "".join(f"<li>{c}</li>" for c in r.semantic_analysis.core_concepts) + "</ul>" if r.semantic_analysis.core_concepts else ""
        arguments_html = ""
        if r.semantic_analysis.key_arguments:
            arguments_html = '<div class="key-points-list">'
            for arg in r.semantic_analysis.key_arguments:
                slide = arg.get("source_slide", 0)
                src = f'<span class="source">(Source: Slide {slide})</span>' if slide else ""
                strength = arg.get("strength", "medium")
                strength_label = {"strong": "强", "medium": "中", "weak": "弱"}.get(strength, strength)
                arguments_html += f'<div class="key-point"><div class="point-header"><strong>{arg.get("argument", "")}</strong> {src}<span class="confidence-medium">{strength_label}</span></div>'
                if arg.get("evidence"):
                    arguments_html += f'<div class="supporting-data">证据：{arg["evidence"]}</div>'
                arguments_html += '</div>'
            arguments_html += '</div>'
        assumptions_html = "<ul>" + "".join(f"<li>{a}</li>" for a in r.semantic_analysis.implicit_assumptions) + "</ul>" if r.semantic_analysis.implicit_assumptions else ""
        semantic_html = f'''<div class="section semantic-analysis">
<h2>语义分析</h2>
{"<h3>核心概念</h3>" + concepts_html if concepts_html else ""}
{"<h3>主要论点</h3>" + arguments_html if arguments_html else ""}
{"<h3>隐含假设</h3>" + assumptions_html if assumptions_html else ""}
</div>'''
    
    logical_html = ""
    if r.logical_analysis.reasoning_chains or r.logical_analysis.cause_effect_relationships:
        chains_html = ""
        if r.logical_analysis.reasoning_chains:
            chains_html = '<div class="key-points-list">'
            for chain in r.logical_analysis.reasoning_chains:
                validity = chain.get("logical_validity", "")
                validity_label = {"valid": "有效", "questionable": "存疑", "invalid": "无效"}.get(validity, validity)
                slides = chain.get("source_slides", [])
                src = f'<span class="source">(Slides: {", ".join(map(str, slides))})</span>' if slides else ""
                validity_class = "confidence-high" if validity == "valid" else ("confidence-medium" if validity == "questionable" else "confidence-low")
                chains_html += f'<div class="key-point"><div class="point-header"><strong>{chain.get("premise", "")}</strong> → <strong>{chain.get("conclusion", "")}</strong> {src}<span class="{validity_class}">{validity_label}</span></div></div>'
            chains_html += '</div>'
        effects_html = ""
        if r.logical_analysis.cause_effect_relationships:
            effects_html = '<div class="key-points-list">'
            for rel in r.logical_analysis.cause_effect_relationships:
                confidence = rel.get("confidence", "medium")
                confidence_label = {"high": "高", "medium": "中", "low": "低"}.get(confidence, confidence)
                effects_html += f'''<div class="key-point">
<div class="point-header"><strong>原因：</strong>{rel.get("cause", "")}</div>
<div class="supporting-data"><strong>结果：</strong>{rel.get("effect", "")} <span class="confidence-{confidence}">置信度：{confidence_label}</span></div>
</div>'''
            effects_html += '</div>'
        connections_html = "<ul>" + "".join(f"<li>{c}</li>" for c in r.logical_analysis.hidden_connections) + "</ul>" if r.logical_analysis.hidden_connections else ""
        logical_html = f'''<div class="section logical-analysis">
<h2>逻辑分析</h2>
{"<h3>推理链条</h3>" + chains_html if chains_html else ""}
{"<h3>因果关系</h3>" + effects_html if effects_html else ""}
{"<h3>隐含联系</h3>" + connections_html if connections_html else ""}
</div>'''
    
    summary_html = ""
    if r.intelligent_summary.one_sentence_summary:
        insights_html = ""
        if r.intelligent_summary.key_insights:
            insights_html = '<div class="key-points-list">'
            for insight in r.intelligent_summary.key_insights:
                sig = insight.get("significance", "medium")
                sig_label = {"high": "高", "medium": "中", "low": "低"}.get(sig, sig)
                slide = insight.get("source_slide", 0)
                src = f'<span class="source">(Source: Slide {slide})</span>' if slide else ""
                insights_html += f'<div class="key-point"><div class="point-header"><strong>{insight.get("insight", "")}</strong> {src}<span class="confidence-{sig}">{sig_label}</span></div></div>'
            insights_html += '</div>'
        highlights_html = "<ul>" + "".join(f"<li>{h}</li>" for h in r.intelligent_summary.innovation_highlights) + "</ul>" if r.intelligent_summary.innovation_highlights else ""
        issues_html = "<ul>" + "".join(f"<li>{i}</li>" for i in r.intelligent_summary.potential_issues) + "</ul>" if r.intelligent_summary.potential_issues else ""
        assessment_html = f"<pre>{r.intelligent_summary.overall_assessment}</pre>" if r.intelligent_summary.overall_assessment else ""
        summary_html = f'''<div class="section intelligent-summary">
<h2>智能总结</h2>
<h3>一句话总结</h3><blockquote>{r.intelligent_summary.one_sentence_summary}</blockquote>
{"<h3>关键洞察</h3>" + insights_html if insights_html else ""}
{"<h3>创新亮点</h3>" + highlights_html if highlights_html else ""}
{"<h3>潜在问题</h3>" + issues_html if issues_html else ""}
{"<h3>整体评价</h3>" + assessment_html if assessment_html else ""}
</div>'''

    strengths_html = "<h3>内容亮点</h3><ul>" + "".join(f"<li>{s}</li>" for s in r.insights.strengths) + "</ul>" if r.insights.strengths else ""
    gaps_html = "<h3>信息缺口</h3><ul>" + "".join(f"<li>{g}</li>" for g in r.insights.gaps) + "</ul>" if r.insights.gaps else ""
    recs_html = "<h3>改进建议</h3><ul>" + "".join(f"<li>{rc}</li>" for rc in r.insights.recommendations) + "</ul>" if r.insights.recommendations else ""
    warnings_html = '<div class="warnings"><h3>警告信息</h3><ul>' + "".join(f"<li>{w}</li>" for w in r.warnings) + "</ul></div>" if r.warnings else ""

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><title>{r.overview.title}</title>
<style>
body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;max-width:900px;margin:0 auto;padding:20px;line-height:1.6;color:#333}}
h1{{color:#2c3e50;border-bottom:2px solid #3498db;padding-bottom:10px}}
h2{{color:#34495e;margin-top:30px}}h3{{color:#2c3e50;margin-top:20px;font-size:1.15em}}h4{{color:#555;margin-top:12px;font-size:1.02em;border-left:3px solid #bdc3c7;padding-left:8px}}
.section{{margin:15px 0;padding:12px 15px;background:#fff;border-left:4px solid #3498db;border-radius:4px}}
.section .section{{margin:10px 0 5px 10px;padding:8px 12px;border-left:3px solid #bdc3c7;background:#fafbfc}}
.section .section .section{{margin:8px 0 5px 8px;border-left:2px solid #ddd;background:#f7f8f9}}
.semantic-analysis{{border-left-color:#9b59b6}}
.logical-analysis{{border-left-color:#e67e22}}
.intelligent-summary{{border-left-color:#1abc9c}}
.key-point{{margin:4px 0;padding:4px 0;font-size:0.95em}}
.key-point + .key-point{{border-top:1px dashed #eee}}
.point-header{{display:flex;align-items:baseline;gap:8px;flex-wrap:wrap}}
.point-header strong{{flex:1;min-width:200px}}
.source{{color:#999;font-size:0.85em;white-space:nowrap}}
.key-points-list{{margin:10px 0}}
.confidence-high{{color:#27ae60;font-size:0.8em;padding:2px 6px;background:#e8f5e9;border-radius:3px}}
.confidence-medium{{color:#f39c12;font-size:0.8em;padding:2px 6px;background:#fff3e0;border-radius:3px}}
.confidence-low{{color:#e74c3c;font-size:0.8em;padding:2px 6px;background:#fce4ec;border-radius:3px}}
.confidence-strong{{color:#27ae60;font-size:0.8em;padding:2px 6px;background:#e8f5e9;border-radius:3px}}
.confidence-weak{{color:#e74c3c;font-size:0.8em;padding:2px 6px;background:#fce4ec;border-radius:3px}}
.supporting-data{{color:#666;font-size:0.9em;margin-top:5px}}
blockquote{{background:#f0f8ff;border-left:4px solid #3498db;padding:10px 15px;margin:10px 0;font-style:italic}}
pre{{background:#f8f9fa;padding:15px;border-radius:5px;white-space:pre-wrap;font-family:inherit}}
.warnings{{background:#fff3e0;padding:15px;border-radius:5px;margin:20px 0}}
.footer{{margin-top:40px;padding-top:20px;border-top:1px solid #ddd;color:#7f8c8d;font-size:0.9em}}
</style>
</head>
<body>
<h1>{r.overview.title}</h1>
<div class="overview"><h2>概览</h2><ul>
<li><strong>总页数：</strong>{r.overview.total_slides}</li>
<li><strong>核心主题：</strong>{r.overview.main_topic}</li>
<li><strong>关键主题：</strong>{themes}</li>
</ul></div>
<h2>分析大纲</h2>{sections_html}
{semantic_html}
{logical_html}
{summary_html}
<div class="insights"><h2>洞察分析</h2>{strengths_html}{gaps_html}{recs_html}</div>
{warnings_html}
<div class="footer"><p><em>报告生成时间：{r.timestamp}</em></p><p><em>本报告基于 PPTParser、PPTAnalyst 和 PPTIntelligent 自动生成</em></p></div>
</body></html>"""


def format_report(data: dict[str, Any], output_path: str | Path | None = None, format_type: str = "markdown", intelligent_data: dict[str, Any] | None = None) -> str:
    validate_input(data)
    report = parse_input(data)
    
    # 集成智能分析结果
    if intelligent_data:
        sa = intelligent_data.get("semantic_analysis", {})
        report.semantic_analysis = SemanticAnalysis(
            core_concepts=sa.get("core_concepts", []),
            key_arguments=sa.get("key_arguments", []),
            implicit_assumptions=sa.get("implicit_assumptions", [])
        )
        
        la = intelligent_data.get("logical_analysis", {})
        report.logical_analysis = LogicalAnalysis(
            reasoning_chains=la.get("reasoning_chains", []),
            cause_effect_relationships=la.get("cause_effect_relationships", []),
            hidden_connections=la.get("hidden_connections", [])
        )
        
        ist = intelligent_data.get("intelligent_summary", {})
        report.intelligent_summary = IntelligentSummary(
            one_sentence_summary=ist.get("one_sentence_summary", ""),
            key_insights=ist.get("key_insights", []),
            innovation_highlights=ist.get("innovation_highlights", []),
            potential_issues=ist.get("potential_issues", []),
            overall_assessment=ist.get("overall_assessment", "")
        )
    
    content = format_html(report) if format_type == "html" else format_markdown(report)
    if output_path:
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        Path(output_path).write_text(content, encoding='utf-8')
    return content


def format_from_file(input_path: str | Path, output_path: str | Path | None = None, format_type: str = "markdown", intelligent_path: str | Path | None = None) -> str:
    input_path = Path(input_path)
    if not input_path.exists():
        raise PPTFormattingError(f"文件不存在: {input_path}")
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    intelligent_data = None
    if intelligent_path:
        intelligent_path = Path(intelligent_path)
        if intelligent_path.exists():
            with open(intelligent_path, 'r', encoding='utf-8') as f:
                intelligent_data = json.load(f)
    
    return format_report(data, output_path, format_type, intelligent_data)


if __name__ == "__main__":
    import sys, argparse
    parser = argparse.ArgumentParser(description="PPT 排版输出")
    parser.add_argument("input", help="输入 JSON 路径（outline.json）")
    parser.add_argument("output", nargs="?", help="输出路径")
    parser.add_argument("--format", choices=["markdown", "html"], default="markdown")
    parser.add_argument("--intelligent", help="智能分析 JSON 路径（intelligent.json）")
    args = parser.parse_args()
    try:
        content = format_from_file(args.input, args.output, args.format, args.intelligent)
        if not args.output:
            print(content)
    except PPTFormattingError as e:
        print(json.dumps({"status": "error", "reason": str(e)}))
        sys.exit(1)
