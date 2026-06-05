import os
import yaml
import json
import shutil
from datetime import datetime
from pathlib import Path


class FormatManager:

    def __init__(self, config_dir=None):
        if config_dir is None:
            self.config_dir = Path(__file__).parent.parent.parent / 'format-normalizer' / 'custom'
        else:
            self.config_dir = Path(config_dir)

        self.builtin_configs = {
            'chinese_academic': self.config_dir / 'chinese_academic.yaml',
            'english_academic': self.config_dir / 'english_academic.yaml',
        }

        self.user_configs_dir = self.config_dir / 'user'
        self.user_configs_dir.mkdir(exist_ok=True)

    def list_configs(self):
        configs = []

        for name, path in self.builtin_configs.items():
            if path.exists():
                configs.append({
                    'name': name,
                    'path': str(path),
                    'type': 'builtin',
                    'modified': datetime.fromtimestamp(path.stat().st_mtime).isoformat(),
                })

        for path in self.user_configs_dir.glob('*.yaml'):
            configs.append({
                'name': path.stem,
                'path': str(path),
                'type': 'user',
                'modified': datetime.fromtimestamp(path.stat().st_mtime).isoformat(),
            })

        for path in self.user_configs_dir.glob('*.yml'):
            configs.append({
                'name': path.stem,
                'path': str(path),
                'type': 'user',
                'modified': datetime.fromtimestamp(path.stat().st_mtime).isoformat(),
            })

        return configs

    def load_config(self, name):
        path = self._resolve_config_path(name)
        if path is None:
            return None

        with open(path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)

    def save_config(self, name, config, overwrite=False):
        if name in self.builtin_configs and not overwrite:
            return {
                'success': False,
                'error': f'Cannot overwrite builtin config "{name}". Use save_as_config() to create a new config.',
            }

        path = self.user_configs_dir / f'{name}.yaml'

        if path.exists() and not overwrite:
            return {
                'success': False,
                'error': f'Config "{name}" already exists. Set overwrite=True to overwrite.',
            }

        with open(path, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

        return {
            'success': True,
            'path': str(path),
            'message': f'Config "{name}" saved successfully.',
        }

    def save_as_config(self, name, config):
        path = self.user_configs_dir / f'{name}.yaml'

        with open(path, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

        return {
            'success': True,
            'path': str(path),
            'message': f'Config "{name}" saved as new config.',
        }

    def delete_config(self, name):
        path = self.user_configs_dir / f'{name}.yaml'

        if not path.exists():
            path = self.user_configs_dir / f'{name}.yml'

        if not path.exists():
            return {
                'success': False,
                'error': f'Config "{name}" not found.',
            }

        path.unlink()

        return {
            'success': True,
            'message': f'Config "{name}" deleted successfully.',
        }

    def import_config(self, source_path, name=None):
        source_path = Path(source_path)

        if not source_path.exists():
            return {
                'success': False,
                'error': f'Source file not found: {source_path}',
            }

        try:
            with open(source_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to parse YAML file: {e}',
            }

        if name is None:
            name = source_path.stem

        result = self.save_as_config(name, config)

        if result['success']:
            result['message'] = f'Config imported from "{source_path}" as "{name}".'

        return result

    def export_config(self, name, output_path):
        config = self.load_config(name)
        if config is None:
            return {
                'success': False,
                'error': f'Config "{name}" not found.',
            }

        output_path = Path(output_path)

        with open(output_path, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

        return {
            'success': True,
            'path': str(output_path),
            'message': f'Config "{name}" exported to "{output_path}".',
        }

    def get_config_schema(self):
        return {
            'metadata': {
                'name': 'Template name',
                'description': 'Template description',
                'standard': 'Standard reference (e.g., GB/T 7713.1-2006)',
            },
            'page': {
                'size': 'Page size (A4, Letter, etc.)',
                'margin_top': 'Top margin in cm',
                'margin_bottom': 'Bottom margin in cm',
                'margin_left': 'Left margin in cm',
                'margin_right': 'Right margin in cm',
            },
            'cover': {
                'enabled': 'Enable cover page',
                'school_name': 'School/organization name',
                'logo_path': 'Path to logo image',
                'title': 'Document title',
                'subtitle': 'Document subtitle',
                'info_items': 'List of info items (author, date, etc.)',
            },
            'heading1': {
                'font': 'Font name',
                'size': 'Font size in pt',
                'bold': 'Bold text',
                'alignment': 'Alignment (center, left, right)',
                'color': 'Text color (RGB)',
                'spacing_before': 'Spacing before in pt',
                'spacing_after': 'Spacing after in pt',
            },
            'heading2': {
                'font': 'Font name',
                'size': 'Font size in pt',
                'bold': 'Bold text',
                'alignment': 'Alignment (center, left, right)',
                'color': 'Text color (RGB)',
                'spacing_before': 'Spacing before in pt',
                'spacing_after': 'Spacing after in pt',
            },
            'heading3': {
                'font': 'Font name',
                'size': 'Font size in pt',
                'bold': 'Bold text',
                'alignment': 'Alignment (center, left, right)',
                'color': 'Text color (RGB)',
                'spacing_before': 'Spacing before in pt',
                'spacing_after': 'Spacing after in pt',
            },
            'body': {
                'font_cn': 'Chinese font name',
                'font_en': 'English font name',
                'size': 'Font size in pt',
                'line_spacing': 'Line spacing (single, 1.5, double)',
                'first_line_indent': 'First line indent in characters',
                'alignment': 'Alignment (justify, left, right, center)',
                'spacing_before': 'Spacing before in pt',
                'spacing_after': 'Spacing after in pt',
            },
            'table': {
                'border': 'Border style (three-line, single, none)',
                'header_font_size': 'Header font size in pt',
                'cell_font_size': 'Cell font size in pt',
                'cell_line_spacing': 'Cell line spacing',
                'caption': {
                    'font_size': 'Caption font size in pt',
                    'bold': 'Caption bold text',
                },
            },
            'footnote': {
                'enabled': 'Enable footnote processing',
                'font_size_cn': 'Chinese font size in pt',
                'font_size_en': 'English font size in pt',
                'line_spacing': 'Footnote line spacing',
                'numbering': 'Numbering format (circled, arabic, roman)',
                'restart_per_page': 'Restart numbering each page',
                'separator_length': 'Separator line length in mm',
                'font_name_cn': 'Chinese font name',
                'font_name_en': 'English font name',
                'first_line_indent': 'First line indent in pt',
            },
            'codeblock': {
                'font': 'Code font name',
                'size': 'Code font size in pt',
                'line_spacing': 'Code line spacing',
                'keep_indent': 'Keep original indentation',
            },
            'references': {
                'font': 'Reference font name',
                'size': 'Reference font size in pt',
                'hanging_indent': 'Hanging indent in characters',
            },
            'toc': {
                'enabled': 'Enable table of contents',
                'max_level': 'Maximum heading level',
            },
            'pagination': {
                'widow_control': 'Enable widow control',
                'keep_heading_with_content': 'Keep heading with content',
            },
            'protection': {
                'preserve_formulas': 'Preserve mathematical formulas',
                'preserve_images': 'Preserve images',
                'preserve_tables': 'Preserve tables',
                'preserve_codeblocks': 'Preserve code blocks',
                'preserve_references': 'Preserve references',
                'preserve_relationships': 'Preserve relationships',
                'preserve_xml_structure': 'Preserve XML structure',
            },
        }

    def _resolve_config_path(self, name):
        if name in self.builtin_configs:
            return self.builtin_configs[name]

        user_path = self.user_configs_dir / f'{name}.yaml'
        if user_path.exists():
            return user_path

        user_path = self.user_configs_dir / f'{name}.yml'
        if user_path.exists():
            return user_path

        return None


if __name__ == '__main__':
    import sys

    manager = FormatManager()

    if len(sys.argv) < 2:
        print("Usage: python format_manager.py <command> [args]")
        print("Commands: list, load <name>, save <name> <json_file>, delete <name>, import <file> [name], export <name> <file>")
        sys.exit(1)

    command = sys.argv[1]

    if command == 'list':
        configs = manager.list_configs()
        for config in configs:
            print(f"  [{config['type']}] {config['name']} - {config['modified']}")

    elif command == 'load' and len(sys.argv) >= 3:
        name = sys.argv[2]
        config = manager.load_config(name)
        if config:
            print(yaml.dump(config, default_flow_style=False, allow_unicode=True))
        else:
            print(f"Config '{name}' not found.")

    elif command == 'save' and len(sys.argv) >= 4:
        name = sys.argv[2]
        json_file = sys.argv[3]
        with open(json_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        result = manager.save_config(name, config, overwrite=True)
        print(json.dumps(result, ensure_ascii=False, indent=2))

    elif command == 'delete' and len(sys.argv) >= 3:
        name = sys.argv[2]
        result = manager.delete_config(name)
        print(json.dumps(result, ensure_ascii=False, indent=2))

    elif command == 'import' and len(sys.argv) >= 3:
        source = sys.argv[2]
        name = sys.argv[3] if len(sys.argv) >= 4 else None
        result = manager.import_config(source, name)
        print(json.dumps(result, ensure_ascii=False, indent=2))

    elif command == 'export' and len(sys.argv) >= 4:
        name = sys.argv[2]
        output = sys.argv[3]
        result = manager.export_config(name, output)
        print(json.dumps(result, ensure_ascii=False, indent=2))

    elif command == 'schema':
        schema = manager.get_config_schema()
        print(json.dumps(schema, ensure_ascii=False, indent=2))

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
