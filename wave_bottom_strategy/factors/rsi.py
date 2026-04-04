# -*- coding: utf-8 -*-
"""RSI因子 - 权重10%"""

from typing import Dict, Any
import pandas as pd
import numpy as np

try:
    import talib
    HAS_TALIB = True
except ImportError:
    HAS_TALIB = False

from .base import Factor


class RSIFactor(Factor):
    """RSI相对强弱指标因子"""
    
    def __init__(self, params: Dict[str, Any] = None):
        super().__init__(params)
        self.period = self.params.get('period', 14)
    
    def calculate(self, data: pd.DataFrame) -> pd.DataFrame:
        close = data['close'].values
        
        if HAS_TALIB:
            rsi = talib.RSI(close, timeperiod=self.period)
        else:
            rsi = self._calc_manual(close)
        
        result = pd.DataFrame({'trade_date': data['trade_date'], 'rsi': rsi})
        return result
    
    def _calc_manual(self, close: np.ndarray) -> np.ndarray:
        deltas = np.diff(close)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        rsi = np.zeros(len(close))
        for i in range(self.period, len(close)):
            avg_gain = gains[i-self.period:i].mean()
            avg_loss = losses[i-self.period:i].mean()
            if avg_loss == 0:
                rsi[i] = 100
            else:
                rsi[i] = 100 - 100 / (1 + avg_gain / avg_loss)
        return rsi
    
    def get_score(self, rsi_data: pd.DataFrame) -> pd.Series:
        rsi = rsi_data['rsi']
        score = pd.Series(30.0, index=rsi_data.index)
        score.loc[rsi < 20] = 100
        score.loc[(rsi >= 20) & (rsi < 30)] = 80
        score.loc[(rsi >= 30) & (rsi < 50)] = 50
        return score
    
    @property
    def weight(self) -> float:
        return 0.10