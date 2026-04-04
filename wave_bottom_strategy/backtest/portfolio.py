# -*- coding: utf-8 -*-
"""组合管理"""

from typing import Dict, List
from dataclasses import dataclass, field
from datetime import date


@dataclass
class Position:
    """持仓"""
    ts_code: str
    shares: int
    cost_price: float
    current_price: float = 0.0
    
    @property
    def market_value(self) -> float:
        return self.shares * self.current_price
    
    @property
    def profit(self) -> float:
        return (self.current_price - self.cost_price) * self.shares
    
    @property
    def profit_pct(self) -> float:
        if self.cost_price == 0:
            return 0
        return (self.current_price - self.cost_price) / self.cost_price


class Portfolio:
    """组合管理"""
    
    def __init__(self, initial_capital: float):
        self.initial_capital = initial_capital
        self.cash = initial_capital
        self.positions: Dict[str, Position] = {}
    
    @property
    def total_value(self) -> float:
        return self.cash + sum(p.market_value for p in self.positions.values())
    
    @property
    def total_profit(self) -> float:
        return self.total_value - self.initial_capital
    
    @property
    def total_profit_pct(self) -> float:
        if self.initial_capital == 0:
            return 0
        return self.total_profit / self.initial_capital
    
    def buy(self, ts_code: str, shares: int, price: float) -> bool:
        """买入"""
        amount = shares * price
        if amount > self.cash:
            return False
        
        self.cash -= amount
        
        if ts_code in self.positions:
            pos = self.positions[ts_code]
            total_cost = pos.cost_price * pos.shares + amount
            total_shares = pos.shares + shares
            pos.cost_price = total_cost / total_shares
            pos.shares = total_shares
            pos.current_price = price
        else:
            self.positions[ts_code] = Position(ts_code, shares, price, price)
        
        return True
    
    def sell(self, ts_code: str, shares: int, price: float) -> bool:
        """卖出"""
        if ts_code not in self.positions:
            return False
        
        pos = self.positions[ts_code]
        if shares > pos.shares:
            shares = pos.shares
        
        self.cash += shares * price
        pos.shares -= shares
        
        if pos.shares == 0:
            del self.positions[ts_code]
        
        return True
    
    def update_prices(self, prices: Dict[str, float]):
        """更新价格"""
        for ts_code, price in prices.items():
            if ts_code in self.positions:
                self.positions[ts_code].current_price = price
    
    def get_position(self, ts_code: str) -> Position:
        """获取持仓"""
        return self.positions.get(ts_code)
    
    def get_all_positions(self) -> List[Position]:
        """获取所有持仓"""
        return list(self.positions.values())