#!/usr/bin/env python3
"""
更严格的参数拟合：使用非线性最小二乘/最小化拟合模型参数。

目标：在现有 `fight-data.csv` 上拟合参数，使预测伤害与实际尽可能接近。
模型采用来自 `src/damage.py` 的基本形式，但增加若干可拟合系数。
"""
import numpy as np
import pandas as pd
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.damage import blade_damage_model
import math

try:
    from scipy.optimize import minimize
    SCIPY_OK = True
except Exception:
    SCIPY_OK = False


def clean(df: pd.DataFrame) -> pd.DataFrame:
    df.columns = [c.strip() for c in df.columns]
    df = df.replace({'未知': np.nan, '': np.nan})
    for c in df.columns:
        if df[c].dtype == object:
            df[c] = df[c].astype(str).str.replace('%','').str.replace(',','').str.strip()
            df[c] = df[c].replace({'nan': np.nan})
    for c in df.columns:
        try:
            df[c] = pd.to_numeric(df[c], errors='coerce')
        except Exception:
            pass
    return df


def model_predict_row(row, params):
    # params: [scale, troops_exp, def_exp, atk_mul, bonus_mul, intercept]
    scale, troops_exp, def_exp, atk_mul, bonus_mul, intercept = params
    A_atk = row.get('攻击方武力')
    A_bonus = row.get('攻击方兵刃伤害累计加成')
    if not (A_bonus is None):
        A_bonus = float(A_bonus) / 100.0
    troops = row.get('攻击方兵力')
    D_bonus = row.get('防守方受到兵刃伤害累计加成')
    if not (D_bonus is None):
        D_bonus = float(D_bonus) / 100.0
    # apply multipliers
    atk = (A_atk if A_atk is not None else 0.0) * atk_mul
    bonus = (A_bonus if A_bonus is not None else 0.0) * bonus_mul
    troops = troops if troops is not None else 1.0
    ddef = 1.0
    raw = blade_damage_model(A_atk=atk, A_bonus=bonus, A_troops=troops, A_skill=1.0, W_weapon=1.0, D_bonus=D_bonus, D_def=ddef, scale=scale, troops_exp=troops_exp, def_exp=def_exp, rnd=1.0)
    return raw + intercept


def loss_fn(params, rows):
    preds = []
    trues = []
    for _, r in rows.iterrows():
        true = r.get('防守方受到伤害')
        if pd.isna(true):
            continue
        pred = model_predict_row(r, params)
        preds.append(pred)
        trues.append(float(true))
    preds = np.array(preds, dtype=float)
    trues = np.array(trues, dtype=float)
    if len(trues) == 0:
        return 1e9
    # use RMSE
    return float(np.sqrt(np.mean((preds - trues) ** 2)))


def fit(df):
    rows = df
    # initial guess: use previous good values
    x0 = np.array([2.07, 0.05, 0.5, 1.0, 1.0, 0.0])
    bounds = [(0.001, 10.0), (0.0, 1.0), (0.1, 2.0), (0.1, 10.0), (0.0, 5.0), (-500.0, 500.0)]
    if SCIPY_OK:
        res = minimize(lambda x: loss_fn(x, rows), x0, method='L-BFGS-B', bounds=bounds)
        return res.x, res.fun
    else:
        # fallback: simple random search
        best = x0
        best_score = loss_fn(x0, rows)
        rng = np.random.default_rng(123)
        for _ in range(2000):
            cand = np.array([rng.uniform(b[0], b[1]) for b in bounds])
            sc = loss_fn(cand, rows)
            if sc < best_score:
                best_score = sc
                best = cand
        return best, best_score


def main():
    fn = Path('fight-data.csv')
    if not fn.exists():
        print('找不到 fight-data.csv')
        return
    df = pd.read_csv(fn, encoding='gbk')
    df = clean(df)
    best_params, best_score = fit(df)
    print('最佳参数:', best_params, '得分(RMSE)=', best_score)
    print('\n逐条样本预测:')
    for _, r in df.iterrows():
        true = r.get('防守方受到伤害')
        if pd.isna(true):
            continue
        pred = model_predict_row(r, best_params)
        print('实际=', int(true), '预测=', int(round(pred)), '差=', int(round(pred)) - int(true))


if __name__ == '__main__':
    main()
