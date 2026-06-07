import sys
import json
import argparse
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
import re

SUPPORTED_EXTENSIONS = {'.xlsx', '.xls', '.csv'}
SUPPORTED_REFERENCE_EXTENSIONS = {'.md'}


def scan_files_recursive(path_str: str) -> List[str]:
    """递归扫描目录中的 Excel/CSV 文件"""
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


def load_excel_file(file_path: str, max_rows: Optional[int] = None) -> Optional[pd.DataFrame]:
    """加载 Excel/CSV 文件"""
    path = Path(file_path)
    if not path.exists():
        return None
    
    try:
        if path.suffix.lower() == '.csv':
            try:
                df = pd.read_csv(file_path, dtype=str, encoding='utf-8-sig', nrows=max_rows)
            except UnicodeDecodeError:
                df = pd.read_csv(file_path, dtype=str, encoding='gbk', nrows=max_rows)
        else:
            df = pd.read_excel(file_path, dtype=str, nrows=max_rows)
        return df
    except Exception as e:
        print(f"警告: 无法加载文件 {file_path}: {str(e)}", file=sys.stderr)
        return None


def load_reference_doc(doc_path: str) -> Optional[Dict[str, Any]]:
    """加载并解析 Markdown 参考文档"""
    path = Path(doc_path)
    if not path.exists():
        return None
    
    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 提取章节
        sections = []
        lines = content.split('\n')
        current_section = None
        current_content = []
        
        for line in lines:
            if line.startswith('#'):
                if current_section:
                    sections.append({
                        'title': current_section,
                        'content': '\n'.join(current_content).strip()
                    })
                current_section = line.lstrip('#').strip()
                current_content = []
            else:
                current_content.append(line)
        
        if current_section:
            sections.append({
                'title': current_section,
                'content': '\n'.join(current_content).strip()
            })
        
        # 提取关键词
        key_terms = []
        for section in sections:
            # 从表格中提取术语
            if '|' in section['content']:
                lines = section['content'].split('\n')
                for line in lines:
                    if '|' in line and not line.strip().startswith('|--'):
                        parts = [p.strip() for p in line.split('|') if p.strip()]
                        key_terms.extend(parts)
        
        return {
            'file_name': path.name,
            'file_path': str(path),
            'sections': [s['title'] for s in sections],
            'key_terms': list(set(key_terms))[:20],  # 限制关键词数量
            'content_length': len(content)
        }
    except Exception as e:
        print(f"警告: 无法加载参考文档 {doc_path}: {str(e)}", file=sys.stderr)
        return None


def analyze_numeric_columns(df: pd.DataFrame) -> Dict[str, Any]:
    """分析数值列的统计信息"""
    numeric_stats = {}
    
    for col in df.columns:
        try:
            # 尝试转换为数值类型
            numeric_series = pd.to_numeric(df[col], errors='coerce')
            if numeric_series.notna().sum() > 0:
                numeric_stats[col] = {
                    'count': int(numeric_series.count()),
                    'mean': float(numeric_series.mean()) if numeric_series.count() > 0 else None,
                    'median': float(numeric_series.median()) if numeric_series.count() > 0 else None,
                    'std': float(numeric_series.std()) if numeric_series.count() > 1 else None,
                    'min': float(numeric_series.min()) if numeric_series.count() > 0 else None,
                    'max': float(numeric_series.max()) if numeric_series.count() > 0 else None,
                    'sum': float(numeric_series.sum()) if numeric_series.count() > 0 else None
                }
        except:
            continue
    
    return numeric_stats


def analyze_categorical_columns(df: pd.DataFrame) -> Dict[str, Any]:
    """分析分类列的信息"""
    categorical_stats = {}
    
    for col in df.columns:
        value_counts = df[col].value_counts().head(10)
        if len(value_counts) > 0:
            categorical_stats[col] = {
                'unique_count': int(df[col].nunique()),
                'top_values': value_counts.to_dict(),
                'null_count': int(df[col].isna().sum())
            }
    
    return categorical_stats


def detect_business_direction(df: pd.DataFrame, area: Optional[str] = None) -> str:
    """根据数据特征推测业务方向"""
    columns = [str(col).lower() for col in df.columns]
    all_text = ' '.join(columns)
    
    # 公司相关关键词
    company_keywords = ['销售', '收入', '成本', '利润', '资产', '负债', '员工', '部门', 
                       '客户', '产品', '订单', '发票', '财务', '预算', '工资', '绩效']
    
    # 学术相关关键词
    academic_keywords = ['成绩', '分数', '学生', '教师', '课程', '班级', '学期', '考试',
                        '论文', '研究', '实验', '调查', '学分', '年级', '学科']
    
    company_score = sum(1 for keyword in company_keywords if keyword in all_text)
    academic_score = sum(1 for keyword in academic_keywords if keyword in all_text)
    
    if company_score > academic_score:
        return 'company'
    elif academic_score > company_score:
        return 'academic'
    else:
        return 'general'


def analyze_company_data(df: pd.DataFrame, area: Optional[str] = None) -> Dict[str, Any]:
    """分析公司数据"""
    results = {
        'direction': 'company',
        'area': area or 'general',
        'metrics': {},
        'insights': []
    }
    
    numeric_stats = analyze_numeric_columns(df)
    categorical_stats = analyze_categorical_columns(df)
    
    results['numeric_statistics'] = numeric_stats
    results['categorical_statistics'] = categorical_stats
    
    # 根据区域生成特定洞察
    if area == 'finance':
        results['insights'] = generate_finance_insights(numeric_stats)
    elif area == 'sales':
        results['insights'] = generate_sales_insights(numeric_stats, categorical_stats)
    elif area == 'hr':
        results['insights'] = generate_hr_insights(numeric_stats, categorical_stats)
    else:
        results['insights'] = generate_general_company_insights(numeric_stats, categorical_stats)
    
    return results


def analyze_academic_data(df: pd.DataFrame, area: Optional[str] = None) -> Dict[str, Any]:
    """分析学术数据"""
    results = {
        'direction': 'academic',
        'area': area or 'general',
        'metrics': {},
        'insights': []
    }
    
    numeric_stats = analyze_numeric_columns(df)
    categorical_stats = analyze_categorical_columns(df)
    
    results['numeric_statistics'] = numeric_stats
    results['categorical_statistics'] = categorical_stats
    
    # 根据区域生成特定洞察
    if area == 'grades':
        results['insights'] = generate_grades_insights(numeric_stats, categorical_stats)
    elif area == 'teaching':
        results['insights'] = generate_teaching_insights(numeric_stats, categorical_stats)
    elif area == 'research':
        results['insights'] = generate_research_insights(numeric_stats, categorical_stats)
    else:
        results['insights'] = generate_general_academic_insights(numeric_stats, categorical_stats)
    
    return results


def analyze_general_data(df: pd.DataFrame) -> Dict[str, Any]:
    """通用数据分析"""
    results = {
        'direction': 'general',
        'area': 'general',
        'metrics': {},
        'insights': []
    }
    
    numeric_stats = analyze_numeric_columns(df)
    categorical_stats = analyze_categorical_columns(df)
    
    results['numeric_statistics'] = numeric_stats
    results['categorical_statistics'] = categorical_stats
    results['insights'] = generate_general_insights(numeric_stats, categorical_stats)
    
    return results


def generate_finance_insights(numeric_stats: Dict) -> List[str]:
    """生成财务分析洞察"""
    insights = []
    
    # 检查是否有常见的财务指标列
    for col, stats in numeric_stats.items():
        col_lower = str(col).lower()
        if '收入' in col_lower or '销售' in col_lower:
            insights.append(f"收入/销售额列 '{col}' 的平均值为 {stats['mean']:.2f}")
        elif '成本' in col_lower or '费用' in col_lower:
            insights.append(f"成本/费用列 '{col}' 的平均值为 {stats['mean']:.2f}")
        elif '利润' in col_lower:
            insights.append(f"利润列 '{col}' 的平均值为 {stats['mean']:.2f}")
    
    if not insights:
        insights.append("已识别数值列并计算基本统计指标")
        insights.append("建议结合业务背景文档进行更深入的财务分析")
    
    return insights


def generate_sales_insights(numeric_stats: Dict, categorical_stats: Dict) -> List[str]:
    """生成销售分析洞察"""
    insights = []
    
    for col, stats in numeric_stats.items():
        col_lower = str(col).lower()
        if '销售' in col_lower or '金额' in col_lower or '收入' in col_lower:
            insights.append(f"销售/金额列 '{col}' 的总额为 {stats['sum']:.2f}，平均值为 {stats['mean']:.2f}")
            if stats['max'] and stats['min']:
                insights.append(f"  - 最大值: {stats['max']:.2f}，最小值: {stats['min']:.2f}")
    
    for col, stats in categorical_stats.items():
        if stats['unique_count'] <= 20:
            insights.append(f"分类列 '{col}' 有 {stats['unique_count']} 个唯一值")
    
    if not insights:
        insights.append("已识别数据并计算基本统计指标")
        insights.append("建议结合销售目标和历史数据进行对比分析")
    
    return insights


def generate_hr_insights(numeric_stats: Dict, categorical_stats: Dict) -> List[str]:
    """生成人力资源分析洞察"""
    insights = []
    
    for col, stats in numeric_stats.items():
        col_lower = str(col).lower()
        if '工资' in col_lower or '薪资' in col_lower or '薪酬' in col_lower:
            insights.append(f"薪酬列 '{col}' 的平均值为 {stats['mean']:.2f}，中位数为 {stats['median']:.2f}")
        elif '绩效' in col_lower or '评分' in col_lower:
            insights.append(f"绩效列 '{col}' 的平均值为 {stats['mean']:.2f}")
    
    for col, stats in categorical_stats.items():
        if '部门' in str(col).lower() or '职位' in str(col).lower():
            insights.append(f"部门/职位列 '{col}' 有 {stats['unique_count']} 个类别")
    
    if not insights:
        insights.append("已识别人力资源数据并计算基本统计指标")
        insights.append("建议结合组织架构进行部门对比分析")
    
    return insights


def generate_grades_insights(numeric_stats: Dict, categorical_stats: Dict) -> List[str]:
    """生成成绩分析洞察"""
    insights = []
    
    for col, stats in numeric_stats.items():
        col_lower = str(col).lower()
        if '成绩' in col_lower or '分数' in col_lower or '分' in col_lower:
            insights.append(f"成绩列 '{col}' 的平均分为 {stats['mean']:.2f}，标准差为 {stats['std']:.2f}")
            if stats['mean'] >= 90:
                insights.append(f"  - 平均分达到优秀水平（90分以上）")
            elif stats['mean'] >= 80:
                insights.append(f"  - 平均分处于良好水平（80-89分）")
            elif stats['mean'] >= 60:
                insights.append(f"  - 平均分处于及格水平（60-79分）")
            else:
                insights.append(f"  - 平均分低于及格线，需要关注")
    
    for col, stats in categorical_stats.items():
        if '班级' in str(col).lower() or '学科' in str(col).lower():
            insights.append(f"分类列 '{col}' 有 {stats['unique_count']} 个类别")
    
    if not insights:
        insights.append("已识别成绩数据并计算基本统计指标")
        insights.append("建议结合课程大纲和教学目标进行深入分析")
    
    return insights


def generate_teaching_insights(numeric_stats: Dict, categorical_stats: Dict) -> List[str]:
    """生成教学质量分析洞察"""
    insights = []
    
    for col, stats in numeric_stats.items():
        col_lower = str(col).lower()
        if '评分' in col_lower or '评价' in col_lower or '满意度' in col_lower:
            insights.append(f"评价列 '{col}' 的平均值为 {stats['mean']:.2f}")
    
    for col, stats in categorical_stats.items():
        if '教师' in str(col).lower() or '课程' in str(col).lower():
            insights.append(f"教师/课程列 '{col}' 有 {stats['unique_count']} 个类别")
    
    if not insights:
        insights.append("已识别教学评估数据并计算基本统计指标")
        insights.append("建议结合教学大纲和学生反馈进行综合评估")
    
    return insights


def generate_research_insights(numeric_stats: Dict, categorical_stats: Dict) -> List[str]:
    """生成科研数据分析洞察"""
    insights = []
    
    for col, stats in numeric_stats.items():
        insights.append(f"数值列 '{col}' 的平均值为 {stats['mean']:.2f}，标准差为 {stats['std']:.2f}")
    
    for col, stats in categorical_stats.items():
        if stats['unique_count'] <= 10:
            insights.append(f"分类列 '{col}' 有 {stats['unique_count']} 个类别")
    
    if not insights:
        insights.append("已识别科研数据并计算基本统计指标")
        insights.append("建议结合研究假设和实验设计进行统计检验")
    
    return insights


def generate_general_company_insights(numeric_stats: Dict, categorical_stats: Dict) -> List[str]:
    """生成通用公司数据洞察"""
    insights = []
    
    if numeric_stats:
        insights.append(f"识别到 {len(numeric_stats)} 个数值列")
        for col, stats in list(numeric_stats.items())[:3]:
            insights.append(f"  - {col}: 平均值 {stats['mean']:.2f}")
    
    if categorical_stats:
        insights.append(f"识别到 {len(categorical_stats)} 个分类列")
        for col, stats in list(categorical_stats.items())[:3]:
            insights.append(f"  - {col}: {stats['unique_count']} 个唯一值")
    
    return insights


def generate_general_academic_insights(numeric_stats: Dict, categorical_stats: Dict) -> List[str]:
    """生成通用学术数据洞察"""
    insights = []
    
    if numeric_stats:
        insights.append(f"识别到 {len(numeric_stats)} 个数值列")
        for col, stats in list(numeric_stats.items())[:3]:
            insights.append(f"  - {col}: 平均值 {stats['mean']:.2f}")
    
    if categorical_stats:
        insights.append(f"识别到 {len(categorical_stats)} 个分类列")
        for col, stats in list(categorical_stats.items())[:3]:
            insights.append(f"  - {col}: {stats['unique_count']} 个唯一值")
    
    return insights


def generate_general_insights(numeric_stats: Dict, categorical_stats: Dict) -> List[str]:
    """生成通用数据洞察"""
    insights = []
    
    if numeric_stats:
        insights.append(f"识别到 {len(numeric_stats)} 个数值列")
        for col, stats in list(numeric_stats.items())[:3]:
            insights.append(f"  - {col}: 平均值 {stats['mean']:.2f}")
    
    if categorical_stats:
        insights.append(f"识别到 {len(categorical_stats)} 个分类列")
        for col, stats in list(categorical_stats.items())[:3]:
            insights.append(f"  - {col}: {stats['unique_count']} 个唯一值")
    
    return insights


def analyze_single_file(file_path: str, direction: Optional[str] = None, 
                       area: Optional[str] = None, max_rows: Optional[int] = None) -> Dict[str, Any]:
    """分析单个文件"""
    df = load_excel_file(file_path, max_rows)
    if df is None:
        return {
            'status': 'error',
            'file': file_path,
            'message': '无法加载文件'
        }
    
    # 如果未指定方向，自动检测
    if not direction:
        direction = detect_business_direction(df, area)
    
    # 根据方向进行分析
    if direction == 'company':
        analysis = analyze_company_data(df, area)
    elif direction == 'academic':
        analysis = analyze_academic_data(df, area)
    else:
        analysis = analyze_general_data(df)
    
    return {
        'status': 'success',
        'file': file_path,
        'file_name': Path(file_path).name,
        'row_count': len(df),
        'column_count': len(df.columns),
        'columns': list(df.columns),
        'direction': direction,
        'area': area or 'general',
        'analysis': analysis
    }


def analyze_directory(dir_path: str, direction: Optional[str] = None, 
                     area: Optional[str] = None, max_rows: Optional[int] = None) -> Dict[str, Any]:
    """分析目录中的所有文件"""
    files = scan_files_recursive(dir_path)
    if not files:
        return {
            'status': 'error',
            'message': f'目录中未找到 Excel 或 CSV 文件: {dir_path}'
        }
    
    results = []
    for file_path in files:
        result = analyze_single_file(file_path, direction, area, max_rows)
        results.append(result)
    
    return {
        'status': 'success',
        'root_dir': dir_path,
        'total_files': len(results),
        'files': results
    }


def main():
    parser = argparse.ArgumentParser(
        description="增强数据分析技能 - 支持按业务需求进行数据比对分析"
    )
    parser.add_argument("data_path", help="数据文件或目录路径")
    parser.add_argument("--reference", nargs='*', help="参考 MD 文档路径（可多个）")
    parser.add_argument("--direction", choices=['company', 'academic', 'general'], 
                       help="分析方向: company(公司), academic(学术), general(通用)")
    parser.add_argument("--area", help="分析区域/领域: finance, sales, hr, grades, teaching, research 等")
    parser.add_argument("--output", help="JSON 输出路径")
    parser.add_argument("--max-rows", type=int, help="最大加载行数")
    
    args = parser.parse_args()
    
    # 加载参考文档
    reference_docs = []
    if args.reference:
        for ref_path in args.reference:
            ref_doc = load_reference_doc(ref_path)
            if ref_doc:
                reference_docs.append(ref_doc)
    
    # 分析数据
    data_path = Path(args.data_path)
    if data_path.is_dir():
        analysis_result = analyze_directory(args.data_path, args.direction, args.area, args.max_rows)
    elif data_path.is_file():
        analysis_result = analyze_single_file(args.data_path, args.direction, args.area, args.max_rows)
    else:
        print(json.dumps({
            'status': 'error',
            'message': f'路径不存在: {args.data_path}'
        }, ensure_ascii=False, indent=2))
        sys.exit(1)
    
    # 构建最终结果
    final_result = {
        'status': 'success',
        'analysis_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'input_path': args.data_path,
        'direction': args.direction or 'auto-detected',
        'area': args.area or 'general',
        'reference_docs': [doc['file_name'] for doc in reference_docs],
        'data_analysis': analysis_result,
        'reference_summary': {doc['file_name']: doc for doc in reference_docs} if reference_docs else {}
    }
    
    # 确定输出路径
    if args.output:
        output_path = Path(args.output)
    else:
        output_path = Path(args.data_path).parent / 'excel_output' / 'analysis_result.json'
    
    # 确保输出目录存在
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # 保存结果
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(final_result, f, ensure_ascii=False, indent=2)
    
    # 输出结果到标准输出
    print(json.dumps(final_result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
