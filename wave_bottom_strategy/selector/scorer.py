# -*- coding: utf-8 -*-
"""因子打分器"""

from typing import List
import pandas as pd
import logging

from factors.kdj import KDJFactor
from factors.ma import MAFactor
from factors.volume import VolumeFactor

logger = logging.getLogger('factor_scorer')


class FactorScorer:
    """因子打分器"""
    
    def __init__(self):
        self.factors = [
            KDJFactor(),
            MAFactor(),
            VolumeFactor(),
        ]
    
    def score_stock(self, data: pd.DataFrame) -> pd.DataFrame:
        """对股票评分"""
        result = pd.DataFrame()
        result['trade_date'] = data['trade_date'] if 'trade_date' in data.columns else data.index
        result['total_score'] = 50.0
        return result