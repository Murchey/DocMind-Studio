import yaml
import json
from pathlib import Path

template_path = Path("d:\\Projects\\vibecoding\\doc-form-master\\SKILLS\\format-normalizer\\custom\\chinese_academic.yaml")
output_path = Path("d:\\Projects\\vibecoding\\doc-form-master\\workspace\\parsed\\template_config.json")

with open(template_path, "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)

output_path.parent.mkdir(parents=True, exist_ok=True)

with open(output_path, "w", encoding="utf-8") as f:
    json.dump(config, f, ensure_ascii=False, indent=2)

print(f"[INFO] Template config saved to: {output_path}")
