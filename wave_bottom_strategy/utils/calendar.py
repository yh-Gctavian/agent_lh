# -*- coding: utf-8 -*-
"""交易日历"""

from typing import List
from datetime import date
import pandas as pd
import logging

logger = logging.getLogger('calendar')


class TradeCalendar:
    """交易日历"""
    
    def __init__(self):
        self._calendar: pd.DataFrame = None
    
    def load(self, exchange: str = 'SSE') -> List[date]:
        """加载交易日历"""
        try:
            import akshare as ak
            df = ak.tool_trade_date_hist_sina()
            dates = pd.to_datetime(df['trade_date']).dt.date.tolist()
            return dates
        except Exception as e:
            logger.warning(f"加载交易日历失败: {e}")
            return []
    
    def is_trade_day(self, dt: date) -> bool:
        """判断是否为交易日"""
        return dt.weekday() < 5
    
    def get_trade_days(self, start: date, end: date) -> List[date]:
        """获取日期范围内的交易日列表"""
        dates = pd.date_range(start, end, freq='B')
        return [d.date() for d in dates]