# -*- coding: utf-8 -*-
"""MACD factor - 10% weight"""

from typing import Dict, Any
import pandas as pd
import numpy as np

from .base import Factor


class MACDFactor(Factor):
    """MACD Factor"""
    
    def __init__(self, params: Dict[str, Any] = None):
        super().__init__(params)
        self.fast = self.params.get('fast', 12)
        self.slow = self.params.get('slow', 26)
        self.signal = self.params.get('signal', 9)
    
    def calculate(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculate MACD"""
        close = data['close'].values
        
        ema12 = self._ema(close, 12)
        ema26 = self._ema(close, 26)
        dif = ema12 - ema26
        dea = self._ema(dif, 9)
        macd = dif - dea
        
        return pd.DataFrame({
            'trade_date': data['trade_date'] if 'trade_date' in data.columns else data.index,
            'dif': dif, 'dea': dea, 'macd': macd * 2
        })
    
    def _ema(self, data, period):
        """Calculate EMA"""
        result = np.zeros(len(data))
        result[0] = data[0]
        k = 2.0 / (period + 1)
        for i in range(1, len(data)):
            result[i] = data[i] * k + result[i-1] * (1 - k)
        return result
    
    def get_score(self, macd_data):
        """Calculate factor score"""
        macd = macd_data['macd']
        score = pd.Series(40.0, index=macd_data.index)
        score.loc[macd < 0] = 60
        score.loc[macd < -0.5] = 80
        return score
    
    @property
    def weight(self) -> float:
        return 0.10