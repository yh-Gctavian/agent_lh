# -*- coding: utf-8 -*-
"""KDJ因子 - 核心因子权重45%"""

from typing import Dict, Any
import pandas as pd
import numpy as np

from .base import Factor


class KDJFactor(Factor):
    """KDJ随机指标因子"""
    
    def __init__(self, params: Dict[str, Any] = None):
        super().__init__(params)
        self.n = self.params.get('n', 9)
        self.m1 = self.params.get('m1', 3)
        self.m2 = self.params.get('m2', 3)
    
    def calculate(self, data: pd.DataFrame) -> pd.DataFrame:
        """计算KDJ值"""
        high = data['high'].values
        low = data['low'].values
        close = data['close'].values
        
        k, d = self._calc_kdj(high, low, close)
        j = 3 * k - 2 * d
        
        return pd.DataFrame({
            'trade_date': data['trade_date'] if 'trade_date' in data.columns else data.index,
            'k': k, 'd': d, 'j': j
        })
    
    def _calc_kdj(self, high, low, close):
        """手动计算KDJ"""
        n = self.n
        rsv = np.zeros(len(close))
        
        for i in range(n - 1, len(close)):
            high_n = high[i-n+1:i+1].max()
            low_n = low[i-n+1:i+1].min()
            if high_n != low_n:
                rsv[i] = (close[i] - low_n) / (high_n - low_n) * 100
        
        k = self._sma(rsv, self.m1)
        d = self._sma(k, self.m2)
        return k, d
    
    def _sma(self, data, period):
        """简单移动平均"""
        result = np.zeros(len(data))
        result[period-1] = data[:period].mean()
        for i in range(period, len(data)):
            result[i] = (result[i-1] * (period - 1) + data[i]) / period
        return result
    
    def get_score(self, kdj_data):
        """计算因子得分"""
        j = kdj_data['j']
        score = pd.Series(30.0, index=kdj_data.index)
        score.loc[j < 20] = 100
        score.loc[(j >= 20) & (j < 30)] = 80
        score.loc[(j >= 30) & (j < 50)] = 50
        return score
    
    @property
    def weight(self) -> float:
        return 0.45