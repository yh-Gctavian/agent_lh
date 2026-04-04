# -*- coding: utf-8 -*-
"""Factor scorer module"""

from typing import List, Dict
import pandas as pd

from factors.kdj import KDJFactor
from factors.ma import MAFactor
from factors.volume import VolumeFactor
from factors.rsi import RSIFactor
from factors.macd import MACDFactor
from factors.bollinger import BollingerFactor


class FactorScorer:
    """Factor scorer - Calculate 6 factors and weighted score"""
    
    def __init__(self):
        self.factors = [
            KDJFactor(), VolumeFactor(), MAFactor(),
            RSIFactor(), MACDFactor(), BollingerFactor()
        ]
    
    def score_stock(self, data: pd.DataFrame) -> pd.DataFrame:
        """Score a single stock"""
        result = pd.DataFrame()
        result['trade_date'] = data['trade_date'] if 'trade_date' in data.columns else data.index
        
        total_score = pd.Series(0.0, index=data.index)
        
        for factor in self.factors:
            try:
                factor_data = factor.calculate(data)
                score = factor.get_score(factor_data)
                result['%s_score' % factor.name] = score
                total_score = total_score + score * factor.weight
            except Exception as e:
                pass
        
        result['total_score'] = total_score
        return result