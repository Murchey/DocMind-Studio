import sys
import json
import argparse
import pandas as pd
from pathlib import Path

SUPPORTED_EXTENSIONS = {'.xlsx', '.xls', '.csv'}


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


def profile_excel(file_path):
    path = Path(file_path)
    
    if not path.exists():
        return json.dumps({"status": "error", "message": f"文件不存在: {file_path}"}, ensure_ascii=False)
    
    if path.suffix.lower() not in ['.xlsx', '.xls', '.csv']:
        return json.dumps({"status": "error", "message": "仅支持 .xlsx, .xls 或 .csv 文件"}, ensure_ascii=False)

    try:
        if path.suffix.lower() == '.csv':
            try:
                df = pd.read_csv(file_path, dtype=str, encoding='utf-8-sig')
            except UnicodeDecodeError:
                df = pd.read_csv(file_path, dtype=str, encoding='gbk')
        else:
            df = pd.read_excel(file_path, dtype=str)

        profile_result = {
            "status": "success",
            "file_name": path.name,
            "file_path": str(path),
            "total_rows": len(df),
            "total_cols": len(df.columns),
            "columns": {}
        }

        for col in df.columns:
            col_data = df[col]
            valid_samples = col_data.dropna().astype(str).unique()
            samples = valid_samples[:3].tolist() if len(valid_samples) > 0 else []

            profile_result["columns"][col] = {
                "type": str(col_data.dtype),
                "null_count": int(col_data.isna().sum()),
                "unique_count": int(col_data.nunique(dropna=True)),
                "sample_values": samples
            }

        return json.dumps(profile_result, ensure_ascii=False, indent=2)

    except Exception as e:
        return json.dumps({"status": "error", "message": f"解析失败: {str(e)}"}, ensure_ascii=False)


def profile_directory(dir_path):
    files = scan_files_recursive(dir_path)
    if not files:
        return json.dumps({"status": "error", "message": f"目录中未找到 Excel 或 CSV 文件: {dir_path}"}, ensure_ascii=False)

    root = Path(dir_path)
    results = []
    for fp in files:
        p = Path(fp)
        rel = p.relative_to(root)
        profile_json = profile_excel(fp)
        profile_data = json.loads(profile_json)
        profile_data['relative_path'] = str(rel)
        if len(rel.parts) > 1:
            profile_data['subdir'] = rel.parts[0]
        else:
            profile_data['subdir'] = '_root'
        results.append(profile_data)

    output = {
        "status": "success",
        "root_dir": str(root),
        "total_files": len(results),
        "files": results
    }
    return json.dumps(output, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="提取表格数据特征并输出 JSON")
    parser.add_argument("file_path", help="要探查的 Excel/CSV 文件路径或包含这些文件的目录路径")
    
    args = parser.parse_args()
    
    target = Path(args.file_path)
    if target.is_dir():
        print(profile_directory(args.file_path))
    else:
        print(profile_excel(args.file_path))