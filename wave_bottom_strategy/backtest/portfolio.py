# -*- coding: utf-8 -*-
"""组合管理"""

from typing import Dict, List
from dataclasses import dataclass
from datetime import date


@dataclass
class Position:
    """持仓信息"""
    ts_code: str       # 股票代码
    shares: int        # 持仓股数
    cost_price: float  # 成本价
    current_price: float  # 当前价
    market_value: float   # 市值
    
    @property
    def profit(self) -> float:
        """持仓盈亏"""
        return (self.current_price - self.cost_price) * self.shares
    
    @property
    def profit_pct(self) -> float:
        """盈亏比例"""
        return (self.current_price - self.cost_price) / self.cost_price


class Portfolio:
    """组合管理"""
    
    def __init__(self, initial_capital: float):
        self.initial_capital = initial_capital
        self.cash = initial_capital
        self.positions: Dict[str, Position] = {}
        self.history: List[Dict] = []
    
    @property
    def total_value(self) -> float:
        """总资产"""
        return self.cash + sum(p.market_value for p in self.positions.values())
    
    @property
    def total_profit(self) -> float:
        """总盈亏"""
        return self.total_value - self.initial_capital
    
    @property
    def total_profit_pct(self) -> float:
        """总收益率"""
        return self.total_profit / self.initial_capital
    
    def buy(self, ts_code: str, shares: int, price: float) -> bool:
        """买入股票
        
        Args:
            ts_code: 股票代码
            shares: 买入股数
            price: 买入价格
            
        Returns:
            是否成功
        """
        # TODO: 实现买入逻辑
        raise NotImplementedError
    
    def sell(self, ts_code: str, shares: int, price: float) -> bool:
        """卖出股票
        
        Args:
            ts_code: 股票代码
            shares: 卖出股数
            price: 卖出价格
            
        Returns:
            是否成功
        """
        # TODO: 实现卖出逻辑
        raise NotImplementedError
    
    def update_prices(self, prices: Dict[str, float]):
        """更新持仓价格
        
        Args:
            prices: 股票代码 -> 当前价格
        """
        # TODO: 实现价格更新逻辑
        raise NotImplementedError
    
    def record(self, trade_date: date):
        """记录当日持仓快照
        
        Args:
            trade_date: 交易日期
        """
        self.history.append({
            'date': trade_date,
            'total_value': self.total_value,
            'cash': self.cash,
            'positions': dict(self.positions)
        })