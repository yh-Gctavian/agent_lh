# -*- coding: utf-8 -*-
"""股票过滤器"""

from typing import List, Set
import pandas as pd


class StockFilter:
    """股票过滤器
    
    剔除不符合条件的股票
    """
    
    def __init__(
        self,
        exclude_st: bool = True,
        exclude_suspended: bool = True,
        exclude_delisted: bool = True
    ):
        self.exclude_st = exclude_st
        self.exclude_suspended = exclude_suspended
        self.exclude_delisted = exclude_delisted
    
    def filter(
        self,
        stock_pool: List[str],
        trade_date: str
    ) -> List[str]:
        """过滤股票池
        
        Args:
            stock_pool: 原始股票池
            trade_date: 交易日期
            
        Returns:
            过滤后的股票池
        """
        result = stock_pool
        
        if self.exclude_st:
            result = self._exclude_st(result)
        
        if self.exclude_suspended:
            result = self._exclude_suspended(result, trade_date)
        
        if self.exclude_delisted:
            result = self._exclude_delisted(result, trade_date)
        
        return result
    
    def _exclude_st(self, stocks: List[str]) -> List[str]:
        """剔除ST股票"""
        # TODO: 实现ST股票过滤
        raise NotImplementedError
    
    def _exclude_suspended(self, stocks: List[str], trade_date: str) -> List[str]:
        """剔除停牌股票"""
        # TODO: 实现停牌股票过滤
        raise NotImplementedError
    
    def _exclude_delisted(self, stocks: List[str], trade_date: str) -> List[str]:
        """剔除退市股票"""
        # TODO: 实现退市股票过滤
        raise NotImplementedError