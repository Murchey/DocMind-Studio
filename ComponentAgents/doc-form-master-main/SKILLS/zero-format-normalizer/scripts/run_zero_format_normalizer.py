import json
import sys
sys.path.insert(0, "d:\\Projects\\vibecoding\\doc-form-master\\SKILLS\\zero-format-normalizer\\scripts")

from zero_format_normalizer import ZeroFormatNormalizer

edited_config = {
    "paper_type": "chinese_academic",
    "fonts": {
        "chinese": {"family": "宋体", "size": 12},
        "english": {"family": "Times New Roman", "size": 12},
        "heading": {"family": "黑体"}
    },
    "heading": {
        "level1": {"font": "黑体", "size": 16, "bold": True, "alignment": "center", "color": "#000000", "spacing_before": 24, "spacing_after": 18},
        "level2": {"font": "黑体", "size": 14, "bold": True, "alignment": "left", "color": "#000000", "spacing_before": 18, "spacing_after": 12},
        "level3": {"font": "黑体", "size": 13, "bold": True, "alignment": "left", "color": "#000000", "spacing_before": 12, "spacing_after": 6}
    },
    "paragraph": {"alignment": "justify", "line_spacing": 1.5, "first_indent": 2, "paragraph_spacing": False},
    "page": {"margin_top": 2.54, "margin_bottom": 2.54, "margin_left": 3.18, "margin_right": 3.18},
    "toc": {
        "enabled": True,
        "title": "目  录",
        "title_font": "黑体",
        "title_size": 16,
        "entry_font": "宋体",
        "entry_size": 12,
        "max_level": 3,
        "indent_step": 2,
        "dot_leaders": True
    },
    "header": {
        "enabled": True,
        "text": "",
        "font": "宋体",
        "size": 9,
        "alignment": "center",
        "separator_line": True
    },
    "footer": {
        "enabled": True,
        "page_number_format": "arabic",
        "font": "宋体",
        "size": 9,
        "alignment": "center"
    },
    "cover": {
        "enabled": True,
        "title": {
            "text": "课程作业",
            "font": "黑体",
            "size": 22,
            "bold": True,
            "alignment": "center",
            "color": "#000000"
        },
        "info_items": [
            {"label": "学号", "value": "111", "font": "宋体", "size": 14},
            {"label": "姓名", "value": "wsq", "font": "宋体", "size": 14},
            {"label": "学院", "value": "软件", "font": "宋体", "size": 14},
            {"label": "专业", "value": "大数据", "font": "宋体", "size": 14},
            {"label": "指导教师", "value": "", "font": "宋体", "size": 14},
            {"label": "日期", "value": "", "font": "宋体", "size": 14}
        ],
        "logo": {
            "enabled": False,
            "image_data": "",
            "width": 120,
            "height": 120,
            "position": "top"
        },
        "layout": {
            "vertical_align": "center",
            "spacing_after_title": 60,
            "spacing_between_items": 10
        }
    }
}

config_path = "d:\\Projects\\vibecoding\\doc-form-master\\workspace\\parsed\\edited_config.json"
with open(config_path, "w", encoding="utf-8") as f:
    json.dump(edited_config, f, ensure_ascii=False, indent=2)

print(f"[INFO] Edited config saved to: {config_path}")

input_path = "d:\\Projects\\vibecoding\\doc-form-master\\workspace\\input\\2029年中国AI与数据要素双轮驱动下的数据科学与大数据技术专业人才竞争力与学业研判报告.docx"
output_path = "d:\\Projects\\vibecoding\\doc-form-master\\workspace\\output\\final.docx"

normalizer = ZeroFormatNormalizer(input_path, config_path)
result = normalizer.run(output_path)

print(f"[INFO] Result: {json.dumps(result, indent=2)}")
