# -*- coding: utf-8 -*-
"""布林带因子 - 权重5%"""

from typing import Dict, Any
import pandas as pd
import numpy as np

from .base import Factor


class BollingerFactor(Factor):
    """布林带因子"""
    
    def __init__(self, params: Dict[str, Any] = None):
        super().__init__(params)
        self.period = self.params.get('period', 20)
        self.std_dev = self.params.get('std_dev', 2.0)
    
    def calculate(self, data: pd.DataFrame) -> pd.DataFrame:
        close = data['close'].values
        mid = np.zeros(len(close))
        upper = np.zeros(len(close))
        lower = np.zeros(len(close))
        
        for i in range(self.period - 1, len(close)):
            mid[i] = close[i-self.period+1:i+1].mean()
            std = close[i-self.period+1:i+1].std()
            upper[i] = mid[i] + self.std_dev * std
            lower[i] = mid[i] - self.std_dev * std
        
        result = pd.DataFrame({
            'trade_date': data['trade_date'],
            'upper': upper,
            'mid': mid,
            'lower': lower
        })
        result['bb_pos'] = (close - lower) / (upper - lower) * 100
        return result
    
    def get_score(self, bb_data: pd.DataFrame) -> pd.Series:
        bb_pos = bb_data['bb_pos']
        score = pd.Series(40.0, index=bb_data.index)
        score.loc[bb_pos < 10] = 90
        score.loc[(bb_pos >= 10) & (bb_pos < 20)] = 80
        return score
    
    @property
    def weight(self) -> float:
        return 0.05