# -*- coding: utf-8 -*-
"""股票过滤器"""

from typing import List, Set
from datetime import datetime
import pandas as pd

try:
    import akshare as ak
except ImportError:
    ak = None

from wave_bottom_strategy.utils.logger import get_logger

logger = get_logger('stock_filter')


class StockFilter:
    """股票过滤器"""
    
    def __init__(
        self,
        exclude_st: bool = True,
        exclude_suspended: bool = True,
        exclude_new: bool = True,
        new_stock_days: int = 60
    ):
        self.exclude_st = exclude_st
        self.exclude_suspended = exclude_suspended
        self.exclude_new = exclude_new
        self.new_stock_days = new_stock_days
        
        self._st_stocks: Set[str] = set()
        self._suspended_stocks: Set[str] = set()
    
    def load_st_stocks(self) -> Set[str]:
        """加载ST股票"""
        if not self._st_stocks and ak:
            try:
                df = ak.stock_zh_a_st_em()
                self._st_stocks = set(df['代码'].tolist())
                logger.info(f"ST股票: {len(self._st_stocks)}只")
            except Exception as e:
                logger.warning(f"加载ST失败: {e}")
        return self._st_stocks
    
    def load_suspended_stocks(self) -> Set[str]:
        """加载停牌股票"""
        if not self._suspended_stocks and ak:
            try:
                df = ak.stock_tfp_em()
                self._suspended_stocks = set(df['代码'].tolist())
                logger.info(f"停牌股票: {len(self._suspended_stocks)}只")
            except Exception as e:
                logger.warning(f"加载停牌失败: {e}")
        return self._suspended_stocks
    
    def filter(self, stock_pool: List[str]) -> List[str]:
        """过滤股票池"""
        result = set(stock_pool)
        
        if self.exclude_st:
            result -= self.load_st_stocks()
        
        if self.exclude_suspended:
            result -= self.load_suspended_stocks()
        
        logger.info(f"过滤: {len(stock_pool)} -> {len(result)}只")
        return list(result)