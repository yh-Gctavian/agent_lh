# -*- coding: utf-8 -*-
"""均线因子 - 权重15%"""

from typing import Dict, Any
import pandas as pd
import numpy as np

from .base import Factor


class MAFactor(Factor):
    """移动平均线因子"""
    
    def __init__(self, params: Dict[str, Any] = None):
        super().__init__(params)
        self.periods = self.params.get('periods', [5, 20, 60])
    
    def calculate(self, data: pd.DataFrame) -> pd.DataFrame:
        close = data['close'].values
        result = pd.DataFrame()
        result['trade_date'] = data['trade_date'] if 'trade_date' in data.columns else data.index
        for period in self.periods:
            ma = np.zeros(len(close))
            for i in range(period - 1, len(close)):
                ma[i] = close[i-period+1:i+1].mean()
            result['ma' + str(period)] = ma
        return result
    
    def get_score(self, ma_data: pd.DataFrame) -> pd.Series:
        return pd.Series(50.0, index=ma_data.index)
    
    @property
    def weight(self) -> float:
        return 0.15