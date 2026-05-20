#!/usr/bin/env python3
"""
合并并清洗战斗数据 CSV 的小工具。

用法示例:
  python scripts/ingest.py --src-dir data/raw --out data/combined_fight_data.csv

脚本会尝试以 GBK 再 UTF-8 解码 CSV 文件，使用 pandas 读取并进行简单清洗：
 - 规范列名空白
 - 替换中文“未知”为空
 - 去除百分号符号（保留原始数值）
 - 合并并去重复
"""
import argparse
from pathlib import Path
import pandas as pd
import numpy as np
import sys


def try_read_csv(path: Path):
    for enc in ("gbk", "utf-8"):
        try:
            return pd.read_csv(path, encoding=enc)
        except Exception:
            continue
    raise RuntimeError(f"无法读取 CSV: {path}")


def clean_df(df: pd.DataFrame) -> pd.DataFrame:
    # 规范列名
    df.columns = [c.strip() for c in df.columns]
    # 将中文未知或空字符串视为 NaN
    df = df.replace({"未知": np.nan, "": np.nan})
    # 去百分号并去掉千分符号（保留可解析的数字）
    for c in df.columns:
        if df[c].dtype == object:
            df[c] = df[c].astype(str).str.replace('%', '').str.replace(',', '').str.strip()
            df[c] = df[c].replace({'nan': np.nan})
    return df


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--src-dir', '-s', type=Path, default=Path('data'), help='包含 CSV 的目录')
    p.add_argument('--out', '-o', type=Path, default=Path('data/combined_fight_data.csv'), help='输出合并文件')
    args = p.parse_args()

    if not args.src_dir.exists():
        print('源目录不存在:', args.src_dir, file=sys.stderr)
        sys.exit(1)

    files = sorted(args.src_dir.glob('*.csv'))
    if not files:
        print('未找到 CSV 文件于', args.src_dir)
        sys.exit(0)

    dfs = []
    for f in files:
        try:
            df = try_read_csv(f)
            df = clean_df(df)
            df['__source_file'] = str(f.name)
            dfs.append(df)
            print('读取:', f.name, '行数=', len(df))
        except Exception as e:
            print('跳过', f.name, '读取失败:', e)

    if not dfs:
        print('没有可合并的数据')
        sys.exit(0)

    combined = pd.concat(dfs, ignore_index=True, sort=False)
    # 去重（基于全部列）
    before = len(combined)
    combined = combined.drop_duplicates()
    after = len(combined)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    combined.to_csv(args.out, index=False, encoding='utf-8')
    print(f'已写出 {args.out}，合并前 {before} 行，合并后 {after} 行')


if __name__ == '__main__':
    main()
