# -*- coding: utf-8 -*-
"""数据预处理器"""

from typing import List, Set
import pandas as pd
import logging

logger = logging.getLogger('data_processor')


class DataProcessor:
    """数据预处理器"""
    
    def __init__(self):
        self.st_stocks: Set[str] = set()
    
    def load_st_stocks(self) -> Set[str]:
        """加载ST股票列表"""
        try:
            import akshare as ak
            df = ak.stock_zh_a_st_em()
            self.st_stocks = set(df['代码'].tolist())
            return self.st_stocks
        except Exception as e:
            logger.warning(f"加载ST股票失败: {e}")
            return set()
    
    def filter_stocks(self, symbols: List[str], exclude_st: bool = True) -> List[str]:
        """过滤股票池"""
        if exclude_st and self.st_stocks:
            return [s for s in symbols if s not in self.st_stocks]
        return symbols
    
    def validate_data(self, df: pd.DataFrame, symbol: str) -> pd.DataFrame:
        """验证数据完整性"""
        if df.empty:
            return df
        df = df.dropna(subset=['open', 'high', 'low', 'close', 'volume'])
        return df
    
    def process_all(self, df: pd.DataFrame, symbol: str) -> pd.DataFrame:
        """执行全部预处理"""
        return self.validate_data(df, symbol)