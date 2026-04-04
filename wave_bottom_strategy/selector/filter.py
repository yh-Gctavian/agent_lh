# -*- coding: utf-8 -*-
"""Stock filter module"""

from typing import List, Set
import logging

logger = logging.getLogger('stock_filter')


class StockFilter:
    """Stock filter - Remove ST, suspended, delisted stocks"""
    
    def __init__(self, exclude_st: bool = True):
        self.exclude_st = exclude_st
        self._st_stocks: Set[str] = set()
    
    def load_st_stocks(self) -> Set[str]:
        """Load ST stock list"""
        try:
            import akshare as ak
            df = ak.stock_zh_a_st_em()
            self._st_stocks = set(df['代码'].tolist())
            logger.info("Loaded ST stocks: %d" % len(self._st_stocks))
        except Exception as e:
            logger.warning("Failed to load ST stocks: %s" % e)
        return self._st_stocks
    
    def filter(self, symbols: List[str]) -> List[str]:
        """Filter stock pool"""
        if self.exclude_st and not self._st_stocks:
            self.load_st_stocks()
        
        result = [s for s in symbols if s not in self._st_stocks]
        return result