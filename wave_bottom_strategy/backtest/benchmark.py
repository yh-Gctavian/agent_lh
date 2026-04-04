# -*- coding: utf-8 -*-
"""基准对比"""

from typing import Dict
import pandas as pd

from utils.logger import get_logger

logger = get_logger('benchmark')


class Benchmark:
    """基准对比（沪深300）"""
    
    def __init__(self, benchmark_code: str = "000300"):
        self.code = benchmark_code
        self.data: pd.DataFrame = None
    
    def load_data(self, start_date: str, end_date: str):
        try:
            import akshare as ak
            df = ak.stock_zh_index_daily(symbol=f"sh{self.code}")
            df = df[(df['date'] >= start_date) & (df['date'] <= end_date)]
            df['return'] = df['close'].pct_change()
            self.data = df
            logger.info(f"加载基准数据: {len(df)}条")
        except Exception as e:
            logger.warning(f"加载基准失败: {e}")
    
    def get_returns(self) -> pd.Series:
        if self.data is not None and 'return' in self.data.columns:
            return self.data['return']
        return pd.Series()
    
    def compare(self, strategy_returns: pd.Series) -> Dict:
        if self.data is None:
            return {}
        
        bench_return = (1 + self.data['return'].dropna()).prod() - 1
        strat_return = (1 + strategy_returns.dropna()).prod() - 1
        
        return {
            'benchmark_return': bench_return,
            'strategy_return': strat_return,
            'excess_return': strat_return - bench_return
        }