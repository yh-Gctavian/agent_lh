# -*- coding: utf-8 -*-
"""RSI factor - 10% weight"""

from typing import Dict, Any
import pandas as pd
import numpy as np

from .base import Factor


class RSIFactor(Factor):
    """RSI Relative Strength Index Factor"""
    
    def __init__(self, params: Dict[str, Any] = None):
        super().__init__(params)
        self.period = self.params.get('period', 14)
    
    def calculate(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculate RSI"""
        close = data['close'].values
        rsi = self._calc_rsi(close, self.period)
        
        return pd.DataFrame({
            'trade_date': data['trade_date'] if 'trade_date' in data.columns else data.index,
            'rsi': rsi
        })
    
    def _calc_rsi(self, close, period):
        """Calculate RSI manually"""
        deltas = np.diff(close)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        rsi = np.zeros(len(close))
        for i in range(period, len(close)):
            avg_gain = gains[i-period:i].mean()
            avg_loss = losses[i-period:i].mean()
            if avg_loss == 0:
                rsi[i] = 100
            else:
                rsi[i] = 100 - 100 / (1 + avg_gain / avg_loss)
        return rsi
    
    def get_score(self, rsi_data):
        """Calculate factor score"""
        rsi = rsi_data['rsi']
        score = pd.Series(30.0, index=rsi_data.index)
        score.loc[rsi < 20] = 100
        score.loc[(rsi >= 20) & (rsi < 30)] = 80
        score.loc[(rsi >= 30) & (rsi < 50)] = 50
        return score
    
    @property
    def weight(self) -> float:
        return 0.10