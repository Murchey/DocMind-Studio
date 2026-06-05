import os
import sys
import argparse
import pandas as pd
from pathlib import Path


def convert_csv_to_excel(src_folder, dest_folder):
    if not os.path.exists(src_folder):
        print(f"❌ 错误: 源文件夹 '{src_folder}' 不存在！")
        sys.exit(1)

    if not os.path.exists(dest_folder):
        os.makedirs(dest_folder)
        print(f"📁 已创建目标文件夹: '{dest_folder}'")

    src_path = Path(src_folder)
    csv_files = [f for f in src_path.rglob('*') if f.is_file() and f.suffix.lower() == '.csv']

    if not csv_files:
        print(f"⚠️ 在 '{src_folder}' 中没有找到 CSV 文件 (.csv)。")
        return

    success_count = 0

    for file_path in csv_files:
        rel_path = file_path.relative_to(src_path)
        print(f"⏳ 正在处理: {rel_path} ...", end=" ")

        dest_subdir = Path(dest_folder) / rel_path.parent
        dest_subdir.mkdir(parents=True, exist_ok=True)

        try:
            try:
                df = pd.read_csv(file_path, dtype=str, encoding='utf-8-sig')
            except UnicodeDecodeError:
                df = pd.read_csv(file_path, dtype=str, encoding='gbk')

            df = df.dropna(how='all', axis=0).dropna(how='all', axis=1)
            
            dest_path = dest_subdir / f"{file_path.stem}.xlsx"

            df.to_excel(dest_path, index=False, engine='openpyxl')
            
            print("✅ 成功")
            success_count += 1

        except Exception as e:
            print(f"❌ 失败! 错误信息: {e}")

    print("-" * 30)
    print(f"🎉 处理完成！共成功转换 {success_count} 个文件。")

if __name__ == "__main__":
    # 配置命令行参数解析
    parser = argparse.ArgumentParser(description="将文件夹中的 CSV 批量安全转换为 Excel")
    parser.add_argument("src", help="源文件夹路径 (包含 CSV 文件)")
    parser.add_argument("dest", help="目标文件夹路径 (用于保存提取后的 Excel 文件)")
    
    args = parser.parse_args()
    
    convert_csv_to_excel(args.src, args.dest)