# -*- coding: utf-8 -*-
"""因子打分器"""

from typing import List, Dict
import pandas as pd
import numpy as np

from factors import KDJFactor, MAFactor, VolumeFactor, RSIFactor, MACDFactor, BollingerFactor
from wave_bottom_strategy.utils.logger import get_logger

logger = get_logger('factor_scorer')


class FactorScorer:
    """因子打分器
    
    计算6因子得分并加权合成总分
    """
    
    def __init__(self):
        self.factors = {
            'kdj': KDJFactor(),
            'ma': MAFactor(),
            'volume': VolumeFactor(),
            'rsi': RSIFactor(),
            'macd': MACDFactor(),
            'bollinger': BollingerFactor()
        }
    
    def calculate_scores(self, data: pd.DataFrame) -> pd.DataFrame:
        """计算所有因子得分
        
        Args:
            data: 日K线数据
            
        Returns:
            各因子得分及综合得分
        """
        result = pd.DataFrame()
        result['trade_date'] = data['trade_date']
        
        total_score = pd.Series(0.0, index=data.index)
        
        for name, factor in self.factors.items():
            # 计算因子值
            factor_data = factor.calculate(data)
            
            # 计算因子得分
            factor_score = factor.get_score(factor_data)
            
            # 加权合成
            total_score += factor_score * factor.weight
            
            # 记录因子得分
            result[f'{name}_score'] = factor_score
        
        # 综合得分
        result['total_score'] = total_score
        
        return result
    
    def rank_stocks(
        self,
        scores_dict: Dict[str, pd.DataFrame],
        trade_date: str,
        top_n: int = 10
    ) -> pd.DataFrame:
        """对股票按得分排序
        
        Args:
            scores_dict: {symbol: scores_df}
            trade_date: 交易日期
            top_n: 返回前N只
            
        Returns:
            排序后的股票列表
        """
        rankings = []
        
        for symbol, scores in scores_dict.items():
            # 获取当日得分
            day_scores = scores[scores['trade_date'] == trade_date]
            if not day_scores.empty:
                rankings.append({
                    'symbol': symbol,
                    'total_score': day_scores['total_score'].iloc[-1],
                    'kdj_score': day_scores['kdj_score'].iloc[-1],
                    'volume_score': day_scores['volume_score'].iloc[-1],
                    'ma_score': day_scores['ma_score'].iloc[-1]
                })
        
        if not rankings:
            return pd.DataFrame()
        
        df = pd.DataFrame(rankings)
        df = df.sort_values('total_score', ascending=False)
        
        return df.head(top_n)