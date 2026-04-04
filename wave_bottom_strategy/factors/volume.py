# -*- coding: utf-8 -*-
"""Volume factor - 15% weight"""

from typing import Dict, Any
import pandas as pd
import numpy as np

from .base import Factor


class VolumeFactor(Factor):
    """Volume Factor"""
    
    def __init__(self, params: Dict[str, Any] = None):
        super().__init__(params)
        self.ma_period = self.params.get('ma_period', 5)
    
    def calculate(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculate volume indicators"""
        volume = data['volume'].values
        
        vol_ma = np.zeros(len(volume))
        for i in range(self.ma_period - 1, len(volume)):
            vol_ma[i] = volume[i-self.ma_period+1:i+1].mean()
        
        vol_ratio = np.zeros(len(volume))
        for i in range(len(volume)):
            if vol_ma[i] > 0:
                vol_ratio[i] = volume[i] / vol_ma[i]
        
        return pd.DataFrame({
            'trade_date': data['trade_date'] if 'trade_date' in data.columns else data.index,
            'volume': volume, 'vol_ma': vol_ma, 'vol_ratio': vol_ratio
        })
    
    def get_score(self, vol_data):
        """Calculate factor score"""
        vol_ratio = vol_data['vol_ratio']
        score = pd.Series(40.0, index=vol_data.index)
        score.loc[vol_ratio < 0.3] = 85
        score.loc[(vol_ratio >= 0.3) & (vol_ratio < 0.5)] = 70
        score.loc[vol_ratio > 2] = 70
        return score
    
    @property
    def weight(self) -> float:
        return 0.15