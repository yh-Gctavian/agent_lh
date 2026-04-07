# -*- coding: utf-8 -*-
"""KDJ因子演示脚本"""

import sys
sys.path.insert(0, '.')

from wave_bottom_strategy.factors.kdj import KDJFactor
import pandas as pd
import numpy as np

print('=== KDJ因子计算演示 ===')
print()

# 创建KDJ因子
kdj = KDJFactor({'n': 9, 'm1': 3, 'm2': 3})
print(f'KDJ参数: N={kdj.n}, M1={kdj.m1}, M2={kdj.m2}')
print(f'因子权重: {kdj.weight*100}%')
print()

# 创建模拟数据
np.random.seed(42)
n = 100
data = pd.DataFrame({
    'trade_date': pd.date_range('2024-01-01', periods=n),
    'high': 10 + np.cumsum(np.random.randn(n) * 0.5),
    'low': 9 + np.cumsum(np.random.randn(n) * 0.5),
    'close': 9.5 + np.cumsum(np.random.randn(n) * 0.5),
})

# 计算KDJ
result = kdj.calculate(data)
print('KDJ计算结果 (最近5天):')
print(result.tail().to_string())
print()

# 计算得分
score = kdj.get_score(result)
print('因子得分 (最近5天):')
print(score.tail().to_string())
print()
print('=== 演示完成 ===')