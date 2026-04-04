# -*- coding: utf-8 -*-
"""股票过滤器"""

from typing import List, Set
import pandas as pd

try:
    import akshare as ak
except ImportError:
    ak = None

from utils.logger import get_logger

logger = get_logger('stock_filter')


class StockFilter:
    """股票过滤器"""
    
    def __init__(self, exclude_st=True, exclude_suspended=True):
        self.exclude_st = exclude_st
        self.exclude_suspended = exclude_suspended
        self._st_stocks: Set[str] = set()
    
    def load_st_stocks(self) -> Set[str]:
        """加载ST股票"""
        if self._st_stocks:
            return self._st_stocks
        try:
            if ak:
                df = ak.stock_zh_a_st_em()
                self._st_stocks = set(df['代码'].tolist())
        except:
            pass
        return self._st_stocks
    
    def load_suspended(self) -> Set[str]:
        """加载停牌股票"""
        try:
            if ak:
                df = ak.stock_tfp_em()
                return set(df['代码'].tolist())
        except:
            return set()
    
    def filter(self, stock_pool: List[str]) -> List[str]:
        """过滤股票池"""
        result = set(stock_pool)
        if self.exclude_st:
            result -= self.load_st_stocks()
        if self.exclude_suspended:
            result -= self.load_suspended()
        return list(result)