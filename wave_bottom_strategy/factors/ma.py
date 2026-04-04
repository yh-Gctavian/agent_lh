# -*- coding: utf-8 -*-
"""MA factor - 15% weight"""

from typing import Dict, Any
import pandas as pd
import numpy as np

from .base import Factor


class MAFactor(Factor):
    """Moving Average Factor"""
    
    def __init__(self, params: Dict[str, Any] = None):
        super().__init__(params)
        self.periods = self.params.get('periods', [5, 20, 60])
    
    def calculate(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculate MA values"""
        close = data['close'].values
        
        result = pd.DataFrame()
        result['trade_date'] = data['trade_date'] if 'trade_date' in data.columns else data.index
        result['close'] = close
        
        for period in self.periods:
            ma = np.zeros(len(close))
            for i in range(period - 1, len(close)):
                ma[i] = close[i-period+1:i+1].mean()
            result['ma%d' % period] = ma
        
        return result
    
    def get_score(self, ma_data):
        """Calculate factor score"""
        close = ma_data['close']
        ma60 = ma_data['ma60']
        
        bias = (close - ma60) / ma60 * 100
        score = pd.Series(30.0, index=ma_data.index)
        score.loc[bias < -20] = 80
        score.loc[(bias >= -20) & (bias < -10)] = 60
        return score
    
    @property
    def weight(self) -> float:
        return 0.15