# -*- coding: utf-8 -*-
"""回测引擎核心"""

from typing import Dict, List, Optional
from datetime import date, datetime
import pandas as pd
import numpy as np

from .portfolio import Portfolio
from .matcher import OrderMatcher, Order
from .benchmark import Benchmark
from selector.engine import SelectorEngine
from data.loader import DataLoader
from utils.logger import get_logger

logger = get_logger('backtest_engine')


class BacktestEngine:
    """回测引擎"""
    
    def __init__(
        self,
        initial_capital: float = 1_000_000.0,
        max_positions: int = 10,
        position_size: float = 0.1
    ):
        self.initial_capital = initial_capital
        self.max_positions = max_positions
        self.position_size = position_size
        
        self.portfolio = Portfolio(initial_capital)
        self.matcher = OrderMatcher()
        self.selector = SelectorEngine()
        self.data_loader = DataLoader()
        
        self.trade_records = []
        self.daily_values = []
    
    def run(self, start_date: str, end_date: str, stock_pool: List[str] = None) -> Dict:
        """运行回测"""
        logger.info(f"开始回测: {start_date} -> {end_date}")
        
        trade_dates = self._get_trade_dates(start_date, end_date)
        
        for i, trade_date in enumerate(trade_dates):
            self._update_prices(trade_date)
            self._record_daily(trade_date)
            
            if i % 5 == 0:  # 每5天调仓
                self._rebalance(trade_date, stock_pool)
        
        return self._calc_result()
    
    def _get_trade_dates(self, start: str, end: str) -> List[date]:
        dates = pd.date_range(start, end, freq='B')  # 工作日
        return [d.date() for d in dates]
    
    def _update_prices(self, trade_date: date):
        prices = {}
        for ts_code in self.portfolio.positions:
            symbol = ts_code.split('.')[0]
            try:
                df = self.data_loader.load_daily_data(symbol, str(trade_date).replace('-',''), str(trade_date).replace('-',''))
                if not df.empty:
                    prices[ts_code] = df['close'].iloc[-1]
            except:
                pass
        self.portfolio.update_prices(prices)
    
    def _record_daily(self, trade_date: date):
        self.daily_values.append({
            'date': trade_date,
            'value': self.portfolio.total_value,
            'cash': self.portfolio.cash
        })
    
    def _rebalance(self, trade_date: date, stock_pool: List[str]):
        try:
            selected = self.selector.run(trade_date, stock_pool, self.max_positions)
            if 'ts_code' in selected.columns:
                target = selected['ts_code'].tolist()
                self._adjust_positions(target)
        except Exception as e:
            logger.warning(f"调仓失败: {e}")
    
    def _adjust_positions(self, target: List[str]):
        current = set(self.portfolio.positions.keys())
        target_set = set(target)
        
        # 卖出
        for code in current - target_set:
            pos = self.portfolio.positions[code]
            self.portfolio.sell(code, pos.shares, pos.current_price)
        
        # 买入
        for code in target_set - current:
            amount = self.portfolio.cash * self.position_size
            price = 10  # 简化
            shares = int(amount / price / 100) * 100
            if shares > 0:
                self.portfolio.buy(code, shares, price)
    
    def _calc_result(self) -> Dict:
        if not self.daily_values:
            return {}
        
        df = pd.DataFrame(self.daily_values)
        df['return'] = df['value'].pct_change()
        df['cum_return'] = (1 + df['return'].fillna(0)).cumprod() - 1
        
        return {
            'initial': self.initial_capital,
            'final': df['value'].iloc[-1],
            'total_return': df['cum_return'].iloc[-1],
            'trades': len(self.trade_records),
            'daily_df': df
        }