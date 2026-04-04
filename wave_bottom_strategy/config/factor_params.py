# -*- coding: utf-8 -*-
"""Factor parameters"""

FACTOR_PARAMS = {
    "kdj": {"n": 9, "m1": 3, "m2": 3, "weight": 0.45},
    "ma": {"periods": [5, 20, 60], "weight": 0.15},
    "volume": {"ma_period": 5, "weight": 0.15},
    "rsi": {"period": 14, "weight": 0.10},
    "macd": {"fast": 12, "slow": 26, "signal": 9, "weight": 0.10},
    "bollinger": {"period": 20, "std_dev": 2.0, "weight": 0.05},
}

SELECTOR_PARAMS = {
    "min_score": 60,
    "max_positions": 10,
    "exclude_st": True,
    "exclude_suspended": True,
}