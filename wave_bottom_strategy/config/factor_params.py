# -*- coding: utf-8 -*-
"""因子参数配置"""

FACTOR_PARAMS = {
    # KDJ 参数
    "kdj": {
        "n": 9,
        "m1": 3,
        "m2": 3,
        "weight": 0.45,  # 45% 权重
    },
    
    # 均线参数
    "ma": {
        "periods": [5, 20, 60],
        "weight": 0.15,  # 15% 权重
    },
    
    # 成交量参数
    "volume": {
        "ma_period": 5,
        "weight": 0.15,  # 15% 权重
    },
    
    # RSI 参数
    "rsi": {
        "period": 14,
        "weight": 0.10,  # 10% 权重
    },
    
    # MACD 参数
    "macd": {
        "fast": 12,
        "slow": 26,
        "signal": 9,
        "weight": 0.10,  # 10% 权重
    },
    
    # 布林带参数
    "bollinger": {
        "period": 20,
        "std_dev": 2.0,
        "weight": 0.05,  # 5% 权重
    },
}

# 选股参数
SELECTOR_PARAMS = {
    # 最小分数阈值
    "min_score": 60,
    
    # 最大持仓数量
    "max_positions": 10,
    
    # 剔除条件
    "exclude_st": True,       # 剔除ST股票
    "exclude_suspended": True, # 剔除停牌股票
    "exclude_delisted": True,  # 剔除退市股票
}