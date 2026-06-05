import sys
import json
import argparse
import webbrowser
import threading
from pathlib import Path
from flask import Flask, render_template, request, jsonify
import pandas as pd

app = Flask(__name__, template_folder='../templates')

SUPPORTED_EXTENSIONS = {'.xlsx', '.xls', '.csv'}

data_store = {
    'mode': None,
    'left_dir': None,
    'right_dir': None,
    'left_files': {},
    'right_files': {},
    'paired_files': [],
    'current_pair': None,
    'output_dir': None,
    'compare_config': None
}


def scan_files_recursive(path_str):
    path = Path(path_str)
    if path.is_file():
        return [str(path)]
    if not path.is_dir():
        return []
    files = []
    for f in path.rglob('*'):
        if f.is_file() and f.suffix.lower() in SUPPORTED_EXTENSIONS:
            files.append(str(f))
    files.sort()
    return files


def detect_header_row(file_path):
    try:
        df_raw = pd.read_excel(file_path, header=None, nrows=10, dtype=str)
        for i in range(min(10, len(df_raw))):
            row = df_raw.iloc[i]
            non_empty = row.dropna()
            non_empty = non_empty[non_empty.str.strip() != '']
            if len(non_empty) >= 3:
                unnamed_count = sum(1 for v in non_empty if str(v).startswith('Unnamed'))
                if unnamed_count < len(non_empty) * 0.5:
                    return i
        return 0
    except:
        return 0


def load_excel_file(file_path, max_rows=None):
    path = Path(file_path)
    if not path.exists():
        return None, f"文件不存在: {file_path}"
    try:
        if path.suffix.lower() == '.csv':
            try:
                df = pd.read_csv(file_path, encoding='utf-8-sig', nrows=max_rows, dtype=str)
            except UnicodeDecodeError:
                df = pd.read_csv(file_path, encoding='gbk', nrows=max_rows, dtype=str)
        else:
            header_row = detect_header_row(file_path)
            df = pd.read_excel(file_path, header=header_row, nrows=max_rows, dtype=str)
        df = df.fillna('')
        return df, None
    except Exception as e:
        return None, f"读取文件失败: {str(e)}"


def load_directory_files(dir_path, max_rows=None):
    files = scan_files_recursive(dir_path)
    result = {}
    for fp in files:
        p = Path(fp)
        df, error = load_excel_file(fp, max_rows)
        if df is not None:
            result[p.name] = {
                'path': fp,
                'name': p.name,
                'df': df,
                'columns': df.columns.tolist(),
                'rows': len(df)
            }
    return result


def clean_records(df, max_rows=200):
    records = df.head(max_rows).to_dict('records')
    clean_records = []
    for row in records:
        clean_row = {}
        for k, v in row.items():
            if pd.isna(v) or v is None:
                clean_row[k] = ''
            else:
                clean_row[k] = str(v)
        clean_records.append(clean_row)
    return clean_records


@app.route('/')
def index():
    return render_template('index.html', mode=data_store['mode'])


@app.route('/api/init')
def init_data():
    paired_files = data_store['paired_files']
    first_pair = paired_files[0] if paired_files else None
    
    result = {
        'mode': data_store['mode'],
        'left_dir': data_store['left_dir'],
        'right_dir': data_store['right_dir'],
        'paired_files': paired_files,
        'current_pair': first_pair,
        'unpaired_left': [f for f in data_store['left_files'].keys() if f not in paired_files],
        'unpaired_right': [f for f in data_store['right_files'].keys() if f not in paired_files]
    }
    
    if first_pair:
        left_info = data_store['left_files'].get(first_pair)
        right_info = data_store['right_files'].get(first_pair)
        if left_info and right_info:
            result['current_columns'] = list(set(left_info['columns']) & set(right_info['columns']))
    
    return jsonify(result)


@app.route('/api/pair')
def get_pair():
    filename = request.args.get('name', '')
    if not filename:
        return jsonify({'status': 'error', 'message': '未指定文件名'})
    
    left_info = data_store['left_files'].get(filename)
    right_info = data_store['right_files'].get(filename)
    
    if not left_info or not right_info:
        return jsonify({'status': 'error', 'message': f'文件对不存在: {filename}'})
    
    data_store['current_pair'] = filename
    
    return jsonify({
        'status': 'success',
        'name': filename,
        'left': {
            'name': filename,
            'path': left_info['path'],
            'columns': left_info['columns'],
            'rows': left_info['rows'],
            'data': clean_records(left_info['df'])
        },
        'right': {
            'name': filename,
            'path': right_info['path'],
            'columns': right_info['columns'],
            'rows': right_info['rows'],
            'data': clean_records(right_info['df'])
        },
        'common_columns': list(set(left_info['columns']) & set(right_info['columns']))
    })


@app.route('/api/confirm', methods=['POST'])
def confirm():
    data = request.json
    primary_key = data.get('primary_key', '')
    secondary_keys = data.get('secondary_keys', [])
    left_value_columns = data.get('left_value_columns', [])
    right_value_columns = data.get('right_value_columns', [])
    notes = data.get('notes', '')
    
    if not primary_key:
        return jsonify({'status': 'error', 'message': '请选择主键列'})
    
    if not left_value_columns and not right_value_columns:
        return jsonify({'status': 'error', 'message': '请至少选择一个值列'})
    
    output_dir = data_store.get('output_dir')
    if not output_dir:
        return jsonify({'status': 'error', 'message': '未设置输出目录'})
    
    config = {
        'left_dir': data_store['left_dir'],
        'right_dir': data_store['right_dir'],
        'paired_files': data_store['paired_files'],
        'primary_key': primary_key,
        'secondary_keys': secondary_keys,
        'left_value_columns': left_value_columns,
        'right_value_columns': right_value_columns,
        'notes': notes
    }
    
    output_path = Path(output_dir) / 'compare_config.json'
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        
        data_store['compare_config'] = config
        
        return jsonify({
            'status': 'success',
            'output_file': str(output_path),
            'paired_count': len(data_store['paired_files']),
            'message': f'比对规则已保存，将对 {len(data_store["paired_files"])} 对同名文件执行比对'
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'保存配置失败: {str(e)}'})


@app.route('/api/shutdown', methods=['POST'])
def shutdown():
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()
    return jsonify({'status': 'success', 'message': '服务已关闭'})


def open_browser(port):
    import time
    time.sleep(1.5)
    webbrowser.open(f'http://localhost:{port}')


def main():
    parser = argparse.ArgumentParser(description='Excel 文件可视化预览与操作')
    parser.add_argument('mode', choices=['compare', 'merge'], help='操作类型：compare（比对）或 merge（合并）')
    parser.add_argument('dirs', nargs='+', help='包含 Excel 文件的目录路径')
    parser.add_argument('--port', type=int, default=5000, help='Web 服务端口号')
    parser.add_argument('--max-rows', type=int, default=None, help='最大加载行数')
    
    args = parser.parse_args()
    
    if args.mode == 'compare' and len(args.dirs) < 2:
        print(json.dumps({
            'status': 'error',
            'message': '比对模式需要两个目录路径'
        }, ensure_ascii=False))
        sys.exit(1)
    
    left_dir = args.dirs[0]
    right_dir = args.dirs[1] if len(args.dirs) > 1 else args.dirs[0]
    
    left_files = load_directory_files(left_dir, args.max_rows)
    right_files = load_directory_files(right_dir, args.max_rows)
    
    if not left_files:
        print(json.dumps({
            'status': 'error',
            'message': f'左侧目录未找到 Excel 文件: {left_dir}'
        }, ensure_ascii=False))
        sys.exit(1)
    
    if not right_files:
        print(json.dumps({
            'status': 'error',
            'message': f'右侧目录未找到 Excel 文件: {right_dir}'
        }, ensure_ascii=False))
        sys.exit(1)
    
    left_names = set(left_files.keys())
    right_names = set(right_files.keys())
    paired = sorted(list(left_names & right_names))
    
    if not paired:
        print(json.dumps({
            'status': 'error',
            'message': '未找到同名文件，请确保两个目录中有相同名称的 Excel 文件',
            'left_files': list(left_files.keys()),
            'right_files': list(right_files.keys())
        }, ensure_ascii=False))
        sys.exit(1)
    
    output_dir = Path(left_dir).parent / 'excel_output'
    output_dir.mkdir(parents=True, exist_ok=True)
    
    data_store['mode'] = args.mode
    data_store['left_dir'] = left_dir
    data_store['right_dir'] = right_dir
    data_store['left_files'] = left_files
    data_store['right_files'] = right_files
    data_store['paired_files'] = paired
    data_store['output_dir'] = str(output_dir)
    data_store['current_pair'] = paired[0]
    
    unpaired_left = list(left_names - right_names)
    unpaired_right = list(right_names - left_names)
    
    print(json.dumps({
        'status': 'success',
        'mode': args.mode,
        'url': f'http://localhost:{args.port}',
        'left_dir': left_dir,
        'right_dir': right_dir,
        'paired_files': paired,
        'paired_count': len(paired),
        'unpaired_left': unpaired_left,
        'unpaired_right': unpaired_right,
        'output_dir': str(output_dir),
        'message': f'找到 {len(paired)} 对同名文件，预览服务已启动，请在浏览器中打开 http://localhost:{args.port}'
    }, ensure_ascii=False))
    
    threading.Thread(target=open_browser, args=(args.port,), daemon=True).start()
    app.run(host='localhost', port=args.port, debug=False)


if __name__ == '__main__':
    main()