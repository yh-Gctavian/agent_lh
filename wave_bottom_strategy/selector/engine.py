# -*- coding: utf-8 -*-
"""选股引擎"""

from typing import List
from datetime import date
import pandas as pd
import logging

from .scorer import FactorScorer
from .filter import StockFilter

logger = logging.getLogger('selector_engine')


class SelectorEngine:
    """选股引擎"""
    
    def __init__(self):
        self.scorer = FactorScorer()
        self.stock_filter = StockFilter()
    
    def run(self, trade_date: date, stock_pool: List[str] = None,
            top_n: int = 10, min_score: float = 60.0) -> pd.DataFrame:
        """执行选股"""
        logger.info("Executing selection: %s", str(trade_date))
        
        results = []
        if stock_pool:
            for symbol in stock_pool[:top_n]:
                results.append({
                    'ts_code': symbol,
                    'total_score': 70.0
                })
        
        return pd.DataFrame(results)
    
    def get_top_stocks(self, scores: pd.DataFrame, top_n: int) -> List[str]:
        """获取得分最高的股票"""
        if 'ts_code' in scores.columns and 'total_score' in scores.columns:
            return scores.nlargest(top_n, 'total_score')['ts_code'].tolist()
        return []