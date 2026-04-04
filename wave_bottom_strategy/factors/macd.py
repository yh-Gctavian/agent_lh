# -*- coding: utf-8 -*-
"""MACD因子 - 权重10%"""

from typing import Dict, Any
import pandas as pd
import numpy as np

try:
    import talib
    HAS_TALIB = True
except ImportError:
    HAS_TALIB = False

from .base import Factor


class MACDFactor(Factor):
    """MACD因子"""
    
    def __init__(self, params: Dict[str, Any] = None):
        super().__init__(params)
        self.fast = self.params.get('fast', 12)
        self.slow = self.params.get('slow', 26)
        self.signal = self.params.get('signal', 9)
    
    def calculate(self, data: pd.DataFrame) -> pd.DataFrame:
        close = data['close'].values
        
        if HAS_TALIB:
            dif, dea, macd = talib.MACD(close, self.fast, self.slow, self.signal)
        else:
            dif, dea, macd = self._calc_manual(close)
        
        result = pd.DataFrame({
            'trade_date': data['trade_date'],
            'dif': dif,
            'dea': dea,
            'macd': macd * 2  # 柱状�?
        })
        return result
    
    def _calc_manual(self, close: np.ndarray) -> tuple:
        ema12 = self._ema(close, 12)
        ema26 = self._ema(close, 26)
        dif = ema12 - ema26
        dea = self._ema(dif, 9)
        macd = dif - dea
        return dif, dea, macd
    
    def _ema(self, data: np.ndarray, period: int) -> np.ndarray:
        result = np.zeros(len(data))
        result[0] = data[0]
        k = 2 / (period + 1)
        for i in range(1, len(data)):
            result[i] = data[i] * k + result[i-1] * (1 - k)
        return result
    
    def get_score(self, macd_data: pd.DataFrame) -> pd.Series:
        macd = macd_data['macd']
        score = pd.Series(40.0, index=macd_data.index)
        # MACD柱负值且逐渐减小（底部回升）
        score.loc[macd < 0] = 60
        score.loc[macd < -0.5] = 80  # 深跌�?
        return score
    
    @property
    def weight(self) -> float:
        return 0.10
