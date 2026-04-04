# -*- coding: utf-8 -*-
"""因子打分器"""

from typing import List, Dict
import pandas as pd

from factors import KDJFactor, MAFactor, VolumeFactor, RSIFactor, MACDFactor, BollingerFactor


class FactorScorer:
    """因子打分器 - 6因子加权打分"""
    
    def __init__(self):
        self.factors = [
            KDJFactor(),    # 45%
            VolumeFactor(), # 15%
            MAFactor(),     # 15%
            RSIFactor(),    # 10%
            MACDFactor(),   # 10%
            BollingerFactor(), # 5%
        ]
    
    def score(self, data: pd.DataFrame) -> pd.DataFrame:
        """计算综合得分
        
        Args:
            data: 日K线数据
            
        Returns:
            包含各因子得分和综合得分的DataFrame
        """
        result = pd.DataFrame()
        result['trade_date'] = data['trade_date']
        
        total_score = pd.Series(0.0, index=data.index)
        
        # 计算各因子得分
        for factor in self.factors:
            factor_data = factor.calculate(data)
            factor_score = factor.get_score(factor_data)
            result[f'{factor.name}_score'] = factor_score
            total_score += factor_score * factor.weight
        
        result['total_score'] = total_score
        
        return result
    
    def get_top_stocks(self, scores: pd.DataFrame, top_n: int = 10) -> List[str]:
        """获取得分最高的N只股票"""
        return scores.nlargest(top_n, 'total_score')['ts_code'].tolist()