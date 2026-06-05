import os
import re
import json
import shutil
import sys
from pathlib import Path
from difflib import SequenceMatcher

SUPPORTED_EXTENSIONS = {'.xlsx', '.xls', '.csv'}

def get_excel_files(directory):
    files = []
    for f in os.listdir(directory):
        if Path(f).suffix.lower() in SUPPORTED_EXTENSIONS:
            files.append(f)
    return sorted(files)

def extract_numbers(filename):
    stem = Path(filename).stem
    numbers = re.findall(r'\d+', stem)
    return [int(n) for n in numbers]

def extract_keywords(filename):
    stem = Path(filename).stem
    stem = re.sub(r'[^\w\u4e00-\u9fff]', ' ', stem)
    keywords = stem.split()
    return [k for k in keywords if len(k) > 0]

def calculate_similarity(str1, str2):
    return SequenceMatcher(None, str1, str2).ratio()

def match_by_numbers(left_files, right_files):
    mapping = []
    used_right = set()
    
    for left_file in left_files:
        left_numbers = extract_numbers(left_file)
        if not left_numbers:
            continue
        
        best_match = None
        best_score = 0
        
        for right_file in right_files:
            if right_file in used_right:
                continue
            
            right_numbers = extract_numbers(right_file)
            if not right_numbers:
                continue
            
            if left_numbers[-1] == right_numbers[-1]:
                score = 1.0
            elif left_numbers[-1] in right_numbers:
                score = 0.8
            else:
                score = 0
            
            if score > best_score:
                best_score = score
                best_match = right_file
        
        if best_match and best_score > 0:
            mapping.append({
                'left': left_file,
                'right': best_match,
                'confidence': best_score,
                'method': 'number'
            })
            used_right.add(best_match)
    
    return mapping

def match_by_keywords(left_files, right_files):
    mapping = []
    used_right = set()
    
    for left_file in left_files:
        left_keywords = extract_keywords(left_file)
        if not left_keywords:
            continue
        
        best_match = None
        best_score = 0
        
        for right_file in right_files:
            if right_file in used_right:
                continue
            
            right_keywords = extract_keywords(right_file)
            if not right_keywords:
                continue
            
            common = set(left_keywords) & set(right_keywords)
            total = set(left_keywords) | set(right_keywords)
            
            if total:
                score = len(common) / len(total)
            else:
                score = 0
            
            if score > best_score:
                best_score = score
                best_match = right_file
        
        if best_match and best_score > 0.3:
            mapping.append({
                'left': left_file,
                'right': best_match,
                'confidence': best_score,
                'method': 'keyword'
            })
            used_right.add(best_match)
    
    return mapping

def match_by_similarity(left_files, right_files):
    mapping = []
    used_right = set()
    
    for left_file in left_files:
        left_stem = Path(left_file).stem
        
        best_match = None
        best_score = 0
        
        for right_file in right_files:
            if right_file in used_right:
                continue
            
            right_stem = Path(right_file).stem
            score = calculate_similarity(left_stem, right_stem)
            
            if score > best_score:
                best_score = score
                best_match = right_file
        
        if best_match and best_score > 0.5:
            mapping.append({
                'left': left_file,
                'right': best_match,
                'confidence': best_score,
                'method': 'similarity'
            })
            used_right.add(best_match)
    
    return mapping

def auto_match(left_files, right_files):
    mapping = match_by_numbers(left_files, right_files)
    
    if len(mapping) >= len(left_files) * 0.8:
        return mapping, 'number'
    
    mapping2 = match_by_keywords(left_files, right_files)
    if len(mapping2) > len(mapping):
        return mapping2, 'keyword'
    
    mapping3 = match_by_similarity(left_files, right_files)
    if len(mapping3) > len(mapping):
        return mapping3, 'similarity'
    
    return mapping, 'number'

def load_manual_config(config_path):
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    return config.get('mapping', [])

def create_renamed_files(left_dir, right_dir, mapping, output_dir):
    left_output = os.path.join(output_dir, 'left')
    right_output = os.path.join(output_dir, 'right')
    
    os.makedirs(left_output, exist_ok=True)
    os.makedirs(right_output, exist_ok=True)
    
    for pair in mapping:
        left_src = os.path.join(left_dir, pair['left'])
        right_src = os.path.join(right_dir, pair['right'])
        
        left_dst = os.path.join(left_output, pair['right'])
        right_dst = os.path.join(right_output, pair['right'])
        
        shutil.copy2(left_src, left_dst)
        shutil.copy2(right_src, right_dst)
    
    return left_output, right_output

def main():
    left_dir = sys.argv[1]
    right_dir = sys.argv[2]
    
    output_dir = None
    strategy = 'auto'
    config_path = None
    
    i = 3
    while i < len(sys.argv):
        if sys.argv[i] == '--output' and i + 1 < len(sys.argv):
            output_dir = sys.argv[i + 1]
            i += 2
        elif sys.argv[i] == '--strategy' and i + 1 < len(sys.argv):
            strategy = sys.argv[i + 1]
            i += 2
        elif sys.argv[i] == '--config' and i + 1 < len(sys.argv):
            config_path = sys.argv[i + 1]
            i += 2
        else:
            i += 1
    
    if not output_dir:
        output_dir = os.path.join(os.path.dirname(left_dir), 'renamed')
    
    left_files = get_excel_files(left_dir)
    right_files = get_excel_files(right_dir)
    
    if not left_files:
        print(json.dumps({
            'status': 'error',
            'message': f'左侧目录没有找到 Excel 文件: {left_dir}'
        }, ensure_ascii=False))
        sys.exit(1)
    
    if not right_files:
        print(json.dumps({
            'status': 'error',
            'message': f'右侧目录没有找到 Excel 文件: {right_dir}'
        }, ensure_ascii=False))
        sys.exit(1)
    
    if strategy == 'manual' and config_path:
        mapping = load_manual_config(config_path)
        used_method = 'manual'
    elif strategy == 'number':
        mapping = match_by_numbers(left_files, right_files)
        used_method = 'number'
    elif strategy == 'keyword':
        mapping = match_by_keywords(left_files, right_files)
        used_method = 'keyword'
    else:
        mapping, used_method = auto_match(left_files, right_files)
    
    paired_left = {m['left'] for m in mapping}
    paired_right = {m['right'] for m in mapping}
    unpaired_left = [f for f in left_files if f not in paired_left]
    unpaired_right = [f for f in right_files if f not in paired_right]
    
    left_output, right_output = create_renamed_files(left_dir, right_dir, mapping, output_dir)
    
    result = {
        'status': 'success',
        'strategy': used_method,
        'total_left': len(left_files),
        'total_right': len(right_files),
        'paired_count': len(mapping),
        'unpaired_left': unpaired_left,
        'unpaired_right': unpaired_right,
        'mapping': mapping,
        'left_dir': left_output,
        'right_dir': right_output,
        'message': f'文件名转换完成，已创建 {len(mapping)} 对同名文件'
    }
    
    if unpaired_left or unpaired_right:
        result['warning'] = f'有 {len(unpaired_left)} 个左侧文件和 {len(unpaired_right)} 个右侧文件未能配对'
    
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    main()