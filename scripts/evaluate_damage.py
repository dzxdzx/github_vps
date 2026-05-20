#!/usr/bin/env python3
"""
评估兵刃伤害模型并用网格搜索优化少量参数。

输出：初始模型误差、优化后误差、每条样本的实际 vs 预测。
"""
import pandas as pd
import numpy as np
from pathlib import Path
import sys
# ensure repo root on path so `src` can be imported
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.damage import predict_from_row
import math


def clean(df: pd.DataFrame) -> pd.DataFrame:
    df.columns = [c.strip() for c in df.columns]
    df = df.replace({'未知': np.nan, '': np.nan})
    # 去百分号
    for c in df.columns:
        if df[c].dtype == object:
            df[c] = df[c].astype(str).str.replace('%','').str.replace(',','').str.strip()
            df[c] = df[c].replace({'nan': np.nan})
    # 转为数值尽量
    for c in df.columns:
        try:
            df[c] = pd.to_numeric(df[c], errors='coerce')
        except Exception:
            pass
    return df


def metrics(y_true, y_pred):
    y_true = np.array(y_true, dtype=float)
    y_pred = np.array(y_pred, dtype=float)
    mae = np.mean(np.abs(y_true - y_pred))
    rmse = math.sqrt(np.mean((y_true - y_pred)**2))
    mape = np.mean(np.abs((y_true - y_pred) / np.maximum(y_true, 1.0))) * 100.0
    return {'MAE': mae, 'RMSE': rmse, 'MAPE%': mape}


def eval_with_params(df, params):
    preds = []
    actual = []
    rows = []
    for _, r in df.iterrows():
        actual_d = r.get('防守方受到伤害')
        if pd.isna(actual_d):
            continue
        pred = predict_from_row(r.to_dict(), params=params)
        preds.append(pred)
        actual.append(float(actual_d))
        rows.append((r.to_dict(), pred, actual_d))
    met = metrics(actual, preds) if preds else {}
    return met, rows


def grid_search(df):
    # 搜索 scale, troops_exp, def_exp
    best = None
    best_params = None
    scales = np.linspace(0.05, 5.0, 50)
    troops_exps = np.linspace(0.0, 1.0, 21)
    def_exps = np.linspace(0.5, 2.0, 16)
    total = len(scales)*len(troops_exps)*len(def_exps)
    i = 0
    for s in scales:
        for te in troops_exps:
            for de in def_exps:
                i += 1
                params = {'scale': float(s), 'troops_exp': float(te), 'def_exp': float(de)}
                met, _ = eval_with_params(df, params)
                if not met:
                    continue
                key = met['RMSE']
                if best is None or key < best:
                    best = key
                    best_params = params
    return best_params, best


def main():
    fn = Path('fight-data.csv')
    if not fn.exists():
        print('找不到 fight-data.csv')
        return
    df = pd.read_csv(fn, encoding='gbk')
    df = clean(df)

    # 只用与兵刃伤害相关的列（若缺则取默认）
    # 初始参数
    init_params = {'scale':1.0, 'troops_exp':0.5, 'def_exp':1.0}
    met_init, rows_init = eval_with_params(df, init_params)
    print('初始参数:', init_params)
    print('初始指标:', met_init)
    print('\n样本对照 (实际 vs 预测):')
    for r, p, a in rows_init:
        print('实际=', a, '预测=', p, '差值=', int(p)-int(a))

    print('\n开始网格搜索优化 scale, troops_exp, def_exp（可能较慢，样本少时很快）...')
    best_params, best_rmse = grid_search(df)
    print('最佳参数:', best_params, '最佳 RMSE:', best_rmse)
    met_best, rows_best = eval_with_params(df, best_params)
    print('优化后指标:', met_best)
    print('\n优化后样本对照:')
    for r, p, a in rows_best:
        print('实际=', a, '预测=', p, '差值=', int(p)-int(a))


if __name__ == '__main__':
    main()
