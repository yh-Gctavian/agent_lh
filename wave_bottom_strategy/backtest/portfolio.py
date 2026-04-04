# -*- coding: utf-8 -*-
"""组合管理"""

from typing import Dict


class Portfolio:
    """组合管理"""
    
    def __init__(self, initial_capital: float):
        self.initial_capital = initial_capital
        self.cash = initial_capital
        self.positions: Dict = {}
    
    @property
    def total_value(self) -> float:
        return self.cash + sum(p['value'] for p in self.positions.values())
    
    def buy(self, ts_code: str, shares: int, price: float) -> bool:
        """买入"""
        amount = shares * price
        if amount > self.cash:
            return False
        self.cash -= amount
        self.positions[ts_code] = {'shares': shares, 'price': price, 'value': amount}
        return True
    
    def sell(self, ts_code: str, shares: int, price: float) -> bool:
        """卖出"""
        if ts_code not in self.positions:
            return False
        self.cash += shares * price
        del self.positions[ts_code]
        return True