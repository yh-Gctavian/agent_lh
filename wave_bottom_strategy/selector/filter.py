# -*- coding: utf-8 -*-
"""股票过滤器"""

from typing import List, Set
import logging

logger = logging.getLogger('stock_filter')


class StockFilter:
    """股票过滤器"""
    
    def __init__(self, exclude_st: bool = True, exclude_suspended: bool = True):
        self.exclude_st = exclude_st
        self.exclude_suspended = exclude_suspended
        self._st_stocks: Set[str] = set()
    
    def load_filter_lists(self):
        """加载过滤列表"""
        try:
            import akshare as ak
            df_st = ak.stock_zh_a_st_em()
            self._st_stocks = set(df_st['代码'].tolist())
        except Exception as e:
            logger.warning(f"加载ST股票失败: {e}")
    
    def filter(self, stock_pool: List[str], trade_date: str = None) -> List[str]:
        """过滤股票池"""
        result = set(stock_pool)
        if self.exclude_st and self._st_stocks:
            result = result - self._st_stocks
        return list(result)