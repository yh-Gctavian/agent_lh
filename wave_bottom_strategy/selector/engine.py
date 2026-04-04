# -*- coding: utf-8 -*-
"""选股引擎"""

from typing import List, Dict
import pandas as pd

from .filter import StockFilter
from .scorer import FactorScorer
from .signal import SignalGenerator
from factors import KDJFactor
from utils.logger import get_logger

logger = get_logger('selector_engine')


class SelectorEngine:
    """选股引擎"""
    
    def __init__(self):
        self.filter = StockFilter()
        self.scorer = FactorScorer()
        self.signal_gen = SignalGenerator()
        self.kdj_factor = KDJFactor()
    
    def run(
        self,
        stock_data: Dict[str, pd.DataFrame],
        trade_date: str
    ) -> pd.DataFrame:
        """执行选股
        
        Args:
            stock_data: {symbol: 日K线DataFrame}
            trade_date: 交易日期
            
        Returns:
            选股结果
        """
        logger.info(f"执行选股: {trade_date}")
        
        results = []
        
        for symbol, data in stock_data.items():
            # 计算得分
            scores = self.scorer.score(data)
            kdj_data = self.kdj_factor.calculate(data)
            
            # 生成信号
            signals = self.signal_gen.generate(scores, kdj_data)
            signals['ts_code'] = symbol
            
            # 取最新一行
            latest = signals.iloc[-1:].copy()
            results.append(latest)
        
        if results:
            result_df = pd.concat(results, ignore_index=True)
            # 按得分排序
            result_df = result_df.sort_values('total_score', ascending=False)
            logger.info(f"选股完成: {len(result_df)}只股票")
            return result_df
        
        return pd.DataFrame()
    
    def select_top(self, result: pd.DataFrame, top_n: int = 10) -> List[str]:
        """选择得分最高的N只股票"""
        buy_signals = result[result['signal'] == 1]
        return buy_signals.head(top_n)['ts_code'].tolist()