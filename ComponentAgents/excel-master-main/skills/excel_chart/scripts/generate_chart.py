import sys
import json
import argparse
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
from pathlib import Path

# 设置中文字体支持
matplotlib.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
matplotlib.rcParams['axes.unicode_minus'] = False

def generate_chart(data_path, chart_type='bar', data_range=None, output_dir=None, max_rows=None):
    """
    基于数据文件生成图表
    
    Args:
        data_path: 数据文件路径（Excel 或 CSV）
        chart_type: 图表类型（bar, line, pie, scatter）
        data_range: 数据范围，JSON 格式字符串，包含 columns, rows, filter 等
        output_dir: 输出目录（可选）
        max_rows: 最大加载行数（可选）
    
    Returns:
        JSON 格式的执行结果
    """
    source = Path(data_path)
    
    # 防呆校验：文件是否存在
    if not source.exists():
        return json.dumps({
            "status": "error",
            "chart_type": chart_type,
            "output_file": "",
            "message": f"文件不存在: {data_path}"
        }, ensure_ascii=False)
    
    # 防呆校验：文件扩展名
    if source.suffix.lower() not in ['.xlsx', '.xls', '.csv']:
        return json.dumps({
            "status": "error",
            "chart_type": chart_type,
            "output_file": "",
            "message": f"仅支持 .xlsx, .xls 或 .csv 文件，当前文件: {source.suffix}"
        }, ensure_ascii=False)
    
    # 防呆校验：图表类型
    valid_chart_types = ['bar', 'line', 'pie', 'scatter']
    if chart_type not in valid_chart_types:
        return json.dumps({
            "status": "error",
            "chart_type": chart_type,
            "output_file": "",
            "message": f"不支持的图表类型: {chart_type}，支持的类型: {', '.join(valid_chart_types)}"
        }, ensure_ascii=False)
    
    try:
        # 读取数据
        if source.suffix.lower() == '.csv':
            try:
                df = pd.read_csv(data_path, encoding='utf-8-sig', nrows=max_rows)
            except UnicodeDecodeError:
                df = pd.read_csv(data_path, encoding='gbk', nrows=max_rows)
        else:
            df = pd.read_excel(data_path, nrows=max_rows)
        
        # 应用数据范围筛选
        if data_range:
            try:
                if isinstance(data_range, str):
                    range_config = json.loads(data_range)
                else:
                    range_config = data_range
                
                # 筛选列
                if 'columns' in range_config and range_config['columns']:
                    valid_columns = [col for col in range_config['columns'] if col in df.columns]
                    if valid_columns:
                        df = df[valid_columns]
                
                # 筛选行范围
                if 'rows' in range_config:
                    rows_config = range_config['rows']
                    start = rows_config.get('start', 0)
                    end = rows_config.get('end', len(df))
                    df = df.iloc[start:end]
                
                # 应用筛选条件
                if 'filter' in range_config:
                    for col, value in range_config['filter'].items():
                        if col in df.columns:
                            df = df[df[col] == value]
                
                # 检查筛选后的数据是否为空
                if df.empty:
                    return json.dumps({
                        "status": "error",
                        "chart_type": chart_type,
                        "output_file": "",
                        "message": "数据范围筛选后无数据"
                    }, ensure_ascii=False)
            except json.JSONDecodeError:
                return json.dumps({
                    "status": "error",
                    "chart_type": chart_type,
                    "output_file": "",
                    "message": "数据范围格式错误，请使用 JSON 格式"
                }, ensure_ascii=False)
            except Exception as e:
                return json.dumps({
                    "status": "error",
                    "chart_type": chart_type,
                    "output_file": "",
                    "message": f"数据范围筛选失败: {str(e)}"
                }, ensure_ascii=False)
        
        # 确定输出目录
        if output_dir:
            output_path = Path(output_dir)
        else:
            # 默认保存到工作区的 excel_output 目录
            # 假设数据文件在 temp 目录，excel_output 在上级目录
            output_path = source.parent.parent / 'excel_output'
        
        # 确保输出目录存在
        output_path.mkdir(parents=True, exist_ok=True)
        
        # 分析数据特征
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
        
        # 如果没有数值列，返回错误
        if not numeric_cols:
            return json.dumps({
                "status": "error",
                "chart_type": chart_type,
                "output_file": "",
                "message": "数据中没有数值列，无法生成图表"
            }, ensure_ascii=False)
        
        # 根据图表类型生成图表
        fig, ax = plt.subplots(figsize=(10, 6))
        
        if chart_type == 'bar':
            # 柱状图：比较不同类别的数值
            if categorical_cols and numeric_cols:
                # 使用第一个分类列作为 x 轴，第一个数值列作为 y 轴
                x_col = categorical_cols[0]
                y_col = numeric_cols[0]
                
                # 按分类列分组计算平均值
                grouped_data = df.groupby(x_col)[y_col].mean()
                
                # 绘制柱状图
                grouped_data.plot(kind='bar', ax=ax, color='steelblue')
                ax.set_title(f'{x_col} - {y_col} 对比图', fontsize=14)
                ax.set_xlabel(x_col, fontsize=12)
                ax.set_ylabel(f'{y_col} (平均值)', fontsize=12)
                ax.tick_params(axis='x', rotation=45)
                
                # 在柱子上显示数值
                for i, v in enumerate(grouped_data):
                    ax.text(i, v + 0.5, f'{v:.1f}', ha='center', va='bottom', fontsize=10)
            else:
                # 如果没有分类列，使用数值列的前几行
                data_to_plot = df[numeric_cols[0]].head(10)
                data_to_plot.plot(kind='bar', ax=ax, color='steelblue')
                ax.set_title(f'{numeric_cols[0]} 数据图', fontsize=14)
                ax.set_xlabel('索引', fontsize=12)
                ax.set_ylabel(numeric_cols[0], fontsize=12)
        
        elif chart_type == 'line':
            # 折线图：展示数据变化趋势
            if len(numeric_cols) >= 1:
                # 使用前几个数值列
                cols_to_plot = numeric_cols[:3]  # 最多显示3条线
                df[cols_to_plot].plot(ax=ax, marker='o')
                ax.set_title('数据变化趋势图', fontsize=14)
                ax.set_xlabel('索引', fontsize=12)
                ax.set_ylabel('数值', fontsize=12)
                ax.legend(cols_to_plot)
                ax.grid(True, alpha=0.3)
            else:
                return json.dumps({
                    "status": "error",
                    "chart_type": chart_type,
                    "output_file": "",
                    "message": "数据中没有足够的数值列生成折线图"
                }, ensure_ascii=False)
        
        elif chart_type == 'pie':
            # 饼图：展示比例关系
            if categorical_cols:
                # 使用第一个分类列统计各类别数量
                col = categorical_cols[0]
                value_counts = df[col].value_counts()
                
                # 绘制饼图
                value_counts.plot(kind='pie', ax=ax, autopct='%1.1f%%', startangle=90)
                ax.set_title(f'{col} 分布图', fontsize=14)
                ax.set_ylabel('')  # 隐藏默认的 ylabel
            else:
                # 如果没有分类列，使用第一个数值列的分布
                col = numeric_cols[0]
                # 将数值分箱
                bins = pd.cut(df[col], bins=5)
                value_counts = bins.value_counts()
                
                value_counts.plot(kind='pie', ax=ax, autopct='%1.1f%%', startangle=90)
                ax.set_title(f'{col} 分布图', fontsize=14)
                ax.set_ylabel('')
        
        elif chart_type == 'scatter':
            # 散点图：展示两个变量的关系
            if len(numeric_cols) >= 2:
                x_col = numeric_cols[0]
                y_col = numeric_cols[1]
                
                ax.scatter(df[x_col], df[y_col], alpha=0.6, color='steelblue')
                ax.set_title(f'{x_col} vs {y_col} 散点图', fontsize=14)
                ax.set_xlabel(x_col, fontsize=12)
                ax.set_ylabel(y_col, fontsize=12)
                ax.grid(True, alpha=0.3)
            else:
                return json.dumps({
                    "status": "error",
                    "chart_type": chart_type,
                    "output_file": "",
                    "message": "数据中没有足够的数值列生成散点图（至少需要2列）"
                }, ensure_ascii=False)
        
        # 调整布局
        plt.tight_layout()
        
        # 生成输出文件名
        chart_type_names = {
            'bar': '柱状图',
            'line': '折线图',
            'pie': '饼图',
            'scatter': '散点图'
        }
        
        # 使用数据文件名和图表类型生成文件名
        filename = f"chart_{source.stem}_{chart_type_names[chart_type]}.png"
        output_file = output_path / filename
        
        # 保存图表
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()
        
        return json.dumps({
            "status": "success",
            "chart_type": chart_type,
            "output_file": str(output_file),
            "message": "图表生成成功"
        }, ensure_ascii=False)
        
    except Exception as e:
        return json.dumps({
            "status": "error",
            "chart_type": chart_type,
            "output_file": "",
            "message": f"图表生成失败: {str(e)}"
        }, ensure_ascii=False)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="基于数据文件生成图表")
    parser.add_argument("data_path", help="数据文件路径（Excel 或 CSV）")
    parser.add_argument("chart_type", nargs='?', default='bar', 
                        choices=['bar', 'line', 'pie', 'scatter'],
                        help="图表类型（可选，默认为 bar）")
    parser.add_argument("data_range", nargs='?', default=None,
                        help="数据范围，JSON 格式字符串（可选）")
    parser.add_argument("output_dir", nargs='?', help="输出目录（可选）")
    parser.add_argument("--max-rows", type=int, default=None, help="最大加载行数（可选）")
    
    args = parser.parse_args()
    
    # 直接 print 结果，Trae 会捕获 stdout 标准输出
    print(generate_chart(args.data_path, args.chart_type, args.data_range, args.output_dir, args.max_rows))