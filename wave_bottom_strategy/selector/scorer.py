# -*- coding: utf-8 -*-
"""因子打分器"""

from typing import List
import pandas as pd
import logging

from wave_bottom_strategy.factors.kdj import KDJFactor
from wave_bottom_strategy.factors.ma import MAFactor
from wave_bottom_strategy.factors.volume import VolumeFactor
from wave_bottom_strategy.factors.rsi import RSIFactor
from wave_bottom_strategy.factors.macd import MACDFactor
from wave_bottom_strategy.factors.bollinger import BollingerFactor

logger = logging.getLogger('factor_scorer')


class FactorScorer:
    """因子打分器"""
    
    def __init__(self):
        self.factors = [
            KDJFactor(),
            MAFactor(),
            VolumeFactor(),
            RSIFactor(),
            MACDFactor(),
            BollingerFactor(),
        ]
    
    def score_stock(self, data: pd.DataFrame) -> pd.DataFrame:
        """对股票评分
        
        Args:
            data: 日K线数据
            
        Returns:
            评分结果DataFrame
        """
        result = pd.DataFrame()
        result['trade_date'] = data['trade_date'] if 'trade_date' in data.columns else data.index
        
        # 计算各因子得分
        total_score = 0.0
        for factor in self.factors:
            try:
                factor_data = factor.calculate(data)
                if not factor_data.empty:
                    score = factor.get_score(factor_data)
                    total_score += score.mean() * factor.weight
            except Exception as e:
                logger.warning(f"因子 {factor.name} 计算失败: {e}")
        
        result['total_score'] = total_score
        return result