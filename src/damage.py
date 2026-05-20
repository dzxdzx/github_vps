import math

def blade_damage_model(A_atk,
                       A_bonus=0.0,
                       A_troops=1,
                       A_skill=1.0,
                       W_weapon=1.0,
                       D_bonus=0.0,
                       D_def=1.0,
                       scale=1.0,
                       troops_exp=0.5,
                       def_exp=1.0,
                       rnd=1.0):
    """可调参数的兵刃伤害模型。

    Damage = round( scale * A_atk * (1+A_bonus) * A_troops**troops_exp * A_skill * W_weapon * (1+D_bonus) / (D_def**def_exp) * rnd )

    参数采用中性默认值以在缺失字段时仍可计算。
    """
    def safe_float(x, default=0.0):
        try:
            v = float(x)
            if math.isnan(v):
                return float(default)
            return v
        except Exception:
            return float(default)

    atk = safe_float(A_atk, 0.0)
    bonus = safe_float(A_bonus, 0.0)
    troops = safe_float(A_troops, 1.0)
    troops = max(1.0, troops)
    skill = safe_float(A_skill, 1.0)
    w = safe_float(W_weapon, 1.0)
    db = safe_float(D_bonus, 0.0)
    ddef = safe_float(D_def, 1.0)

    raw = scale * atk * (1.0 + bonus) * (troops ** troops_exp) * skill * w * (1.0 + db) / (max(ddef, 0.001) ** def_exp) * rnd
    dmg = max(1, int(round(raw)))
    return dmg


def predict_from_row(row, params=None):
    if params is None:
        params = {}
    # map expected column names to model inputs
    A_atk = row.get('攻击方武力')
    # percent fields assumed already cleaned to numeric (e.g., 80.42 -> 80.42)
    A_bonus = row.get('攻击方兵刃伤害累计加成')
    if not (A_bonus is None):
        A_bonus = float(A_bonus) / 100.0
    A_troops = row.get('攻击方兵力')
    A_skill = params.get('A_skill', 1.0)
    W_weapon = params.get('W_weapon', 1.0)
    D_bonus = row.get('防守方受到兵刃伤害累计加成')
    if not (D_bonus is None):
        D_bonus = float(D_bonus) / 100.0
    D_def = params.get('D_def', 1.0)

    return blade_damage_model(A_atk=A_atk,
                              A_bonus=A_bonus,
                              A_troops=A_troops,
                              A_skill=A_skill,
                              W_weapon=W_weapon,
                              D_bonus=D_bonus,
                              D_def=D_def,
                              scale=params.get('scale',1.0),
                              troops_exp=params.get('troops_exp',0.5),
                              def_exp=params.get('def_exp',1.0),
                              rnd=1.0)
