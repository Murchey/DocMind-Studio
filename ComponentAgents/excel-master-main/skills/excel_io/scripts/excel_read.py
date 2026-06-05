import os
import sys
import argparse
import pandas as pd
from pathlib import Path

SUPPORTED_EXTENSIONS = {'.xlsx', '.xls'}


def convert_excel_to_csv(src_folder, dest_folder):
    if not os.path.exists(src_folder):
        print(f"❌ 错误: 源文件夹 '{src_folder}' 不存在！")
        sys.exit(1)

    if not os.path.exists(dest_folder):
        os.makedirs(dest_folder)
        print(f"📁 已创建目标文件夹: '{dest_folder}'")

    src_path = Path(src_folder)
    excel_files = [f for f in src_path.rglob('*') if f.is_file() and f.suffix.lower() in SUPPORTED_EXTENSIONS]

    if not excel_files:
        print(f"⚠️ 在 '{src_folder}' 中没有找到 Excel 文件 (.xlsx 或 .xls)。")
        return

    success_count = 0

    for file_path in excel_files:
        rel_path = file_path.relative_to(src_path)
        print(f"⏳ 正在处理: {rel_path} ...", end=" ")

        dest_subdir = Path(dest_folder) / rel_path.parent
        dest_subdir.mkdir(parents=True, exist_ok=True)

        try:
            excel_data = pd.read_excel(file_path, sheet_name=None, dtype=str)

            for sheet_name, df in excel_data.items():
                df = df.dropna(how='all', axis=0).dropna(how='all', axis=1)
                
                if len(excel_data) == 1:
                    csv_filename = f"{file_path.stem}.csv"
                else:
                    csv_filename = f"{file_path.stem}_{sheet_name}.csv"
                
                dest_path = dest_subdir / csv_filename

                df.to_csv(dest_path, index=False, encoding='utf-8-sig')
            
            print("✅ 成功")
            success_count += 1

        except Exception as e:
            print(f"❌ 失败! 错误信息: {e}")

    print("-" * 30)
    print(f"🎉 处理完成！共成功转换 {success_count} 个文件。")

if __name__ == "__main__":
    # 配置命令行参数解析
    parser = argparse.ArgumentParser(description="将文件夹中的 Excel 批量安全转换为 CSV")
    parser.add_argument("src", help="源文件夹路径 (包含 Excel 文件)")
    parser.add_argument("dest", help="目标文件夹路径 (用于保存提取后的 CSV 文件)")
    
    args = parser.parse_args()
    
    convert_excel_to_csv(args.src, args.dest)