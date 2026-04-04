# -*- coding: utf-8 -*-
"""交易日历"""

from typing import List
from datetime import date
import pandas as pd


class TradeCalendar:
    """交易日历"""
    
    def __init__(self):
        self._calendar: pd.DataFrame = None
    
    def load(self, exchange: str = 'SSE') -> List[date]:
        """加载交易日历
        
        Args:
            exchange: 交易所
            
        Returns:
            交易日列�?
        """
        # TODO: 实现交易日历加载
        # 可从 exchange_calendars 或本地文件加�?
        raise NotImplementedError
    
    def is_trade_day(self, dt: date) -> bool:
        """判断是否为交易日
        
        Args:
            dt: 日期
            
        Returns:
            是否为交易日
        """
        # TODO: 实现交易日判�?
        raise NotImplementedError
    
    def get_next_trade_day(self, dt: date) -> date:
        """获取下一个交易日
        
        Args:
            dt: 当前日期
            
        Returns:
            下一个交易日
        """
        # TODO: 实现逻辑
        raise NotImplementedError
    
    def get_trade_days(self, start: date, end: date) -> List[date]:
        """获取日期范围内的交易日列�?
        
        Args:
            start: 开始日�?
            end: 结束日期
            
        Returns:
            交易日列�?
        """
        # TODO: 实现逻辑
        raise NotImplementedError
