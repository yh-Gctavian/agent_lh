# -*- coding: utf-8 -*-
"""Backtest engine"""

from typing import Dict, List
from datetime import date
import pandas as pd
import logging

logger = logging.getLogger('backtest_engine')


class BacktestEngine:
    """Backtest engine"""
    
    def __init__(self, initial_capital: float = 1000000.0, max_positions: int = 10):
        self.initial_capital = initial_capital
        self.max_positions = max_positions
        self.daily_values: List[Dict] = []
        self.trade_records: List[Dict] = []
    
    def run(self, start_date: str, end_date: str) -> Dict:
        """Run backtest"""
        logger.info("Starting backtest: %s -> %s" % (start_date, end_date))
        
        trade_dates = pd.date_range(start_date, end_date, freq='B')
        
        for trade_date in trade_dates:
            self.daily_values.append({
                'date': trade_date.date(),
                'value': self.initial_capital
            })
        
        return self._calc_result()
    
    def _calc_result(self) -> Dict:
        """Calculate backtest result"""
        if not self.daily_values:
            return {}
        
        df = pd.DataFrame(self.daily_values)
        return {
            'initial': self.initial_capital,
            'final': df['value'].iloc[-1],
            'trades': len(self.trade_records)
        }