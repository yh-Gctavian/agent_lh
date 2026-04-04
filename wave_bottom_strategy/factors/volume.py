# -*- coding: utf-8 -*-
"""成交量因子 - 权重15%"""

from typing import Dict, Any
import pandas as pd
import numpy as np

from .base import Factor


class VolumeFactor(Factor):
    """成交量因子
    
    参数:
        ma_period: 均量周期，默认5
    """
    
    def __init__(self, params: Dict[str, Any] = None):
        super().__init__(params)
        self.ma_period = self.params.get('ma_period', 5)
    
    def calculate(self, data: pd.DataFrame) -> pd.DataFrame:
        volume = data['volume'].values
        close = data['close'].values
        
        result = pd.DataFrame()
        result['trade_date'] = data['trade_date'] if 'trade_date' in data.columns else data.index
        result['volume'] = volume
        
        result['vol_ma'] = self._calculate_ma(volume, self.ma_period)
        result['vol_ratio'] = volume / result['vol_ma']
        
        if 'turn' in data.columns:
            result['turn'] = data['turn']
        
        result['low_vol_days'] = self._count_low_vol_days(volume, result['vol_ma'].values)
        result['is_high_vol'] = result['vol_ratio'] > 2
        result['is_low_vol'] = result['vol_ratio'] < 0.5
        
        return result
    
    def _calculate_ma(self, data: np.ndarray, period: int) -> np.ndarray:
        result = np.zeros(len(data))
        for i in range(period - 1, len(data)):
            result[i] = data[i-period+1:i+1].mean()
        for i in range(period - 1):
            result[i] = data[:i+1].mean() if i > 0 else data[0]
        return result
    
    def _count_low_vol_days(self, volume: np.ndarray, vol_ma: np.ndarray) -> np.ndarray:
        result = np.zeros(len(volume))
        count = 0
        for i in range(len(volume)):
            if vol_ma[i] > 0 and volume[i] < vol_ma[i] * 0.7:
                count += 1
            else:
                count = 0
            result[i] = count
        return result
    
    def get_score(self, vol_data: pd.DataFrame) -> pd.Series:
        low_vol_days = vol_data['low_vol_days']
        vol_ratio = vol_data['vol_ratio']
        
        score = pd.Series(40.0, index=vol_data.index)
        
        score.loc[low_vol_days >= 5] = 90
        score.loc[(low_vol_days >= 3) & (low_vol_days < 5)] = 80
        score.loc[(low_vol_days >= 1) & (low_vol_days < 3)] = 60
        score.loc[vol_ratio > 2] = 70
        score.loc[vol_ratio < 0.3] = 85
        
        return score
    
    @property
    def weight(self) -> float:
        return 0.15