# -*- coding: utf-8 -*-
"""回测引擎"""

from typing import Dict, List
from datetime import date
import pandas as pd
import logging

logger = logging.getLogger('backtest_engine')


class BacktestEngine:
    """回测引擎"""
    
    def __init__(self, initial_capital: float = 1_000_000.0, max_positions: int = 10):
        self.initial_capital = initial_capital
        self.max_positions = max_positions
        self.daily_values: List[Dict] = []
        self.trade_records: List[Dict] = []
    
    def run(self, start_date: str, end_date: str) -> Dict:
        """运行回测"""
        logger.info(f"开始回测: {start_date} -> {end_date}")
        
        trade_dates = pd.date_range(start_date, end_date, freq='B')
        
        for trade_date in trade_dates:
            self.daily_values.append({
                'date': trade_date.date(),
                'value': self.initial_capital
            })
        
        return self._calc_result()
    
    def _calc_result(self) -> Dict:
        """计算回测结果"""
        if not self.daily_values:
            return {}
        
        df = pd.DataFrame(self.daily_values)
        return {
            'initial': self.initial_capital,
            'final': df['value'].iloc[-1],
            'trades': len(self.trade_records)
        }