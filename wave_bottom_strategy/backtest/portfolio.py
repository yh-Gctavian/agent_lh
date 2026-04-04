# -*- coding: utf-8 -*-
"""组合管理"""

from typing import Dict, List
from dataclasses import dataclass, field
from datetime import date
import pandas as pd


@dataclass
class Position:
    """持仓信息"""
    ts_code: str
    shares: int
    cost_price: float
    current_price: float = 0.0
    
    @property
    def market_value(self) -> float:
        return self.current_price * self.shares
    
    @property
    def profit(self) -> float:
        return (self.current_price - self.cost_price) * self.shares
    
    @property
    def profit_pct(self) -> float:
        if self.cost_price == 0:
            return 0
        return (self.current_price - self.cost_price) / self.cost_price


class Portfolio:
    """组合管理
    
    仓位规则：
    - 单票最大10%
    - 最大持仓10只
    - 总仓位上限80%
    """
    
    def __init__(
        self,
        initial_capital: float = 1_000_000,
        max_positions: int = 10,
        single_position_pct: float = 0.10,  # 单票10%
        max_total_position_pct: float = 0.80  # 总仓位80%
    ):
        self.initial_capital = initial_capital
        self.cash = initial_capital
        self.max_positions = max_positions
        self.single_position_pct = single_position_pct
        self.max_total_position_pct = max_total_position_pct
        
        self.positions: Dict[str, Position] = {}
        self.history: List[Dict] = []
        self.trades: List[Dict] = []
    
    @property
    def total_value(self) -> float:
        """总资产"""
        return self.cash + sum(p.market_value for p in self.positions.values())
    
    @property
    def position_value(self) -> float:
        """持仓市值"""
        return sum(p.market_value for p in self.positions.values())
    
    @property
    def position_pct(self) -> float:
        """仓位比例"""
        return self.position_value / self.total_value
    
    @property
    def profit(self) -> float:
        """总盈亏"""
        return self.total_value - self.initial_capital
    
    @property
    def profit_pct(self) -> float:
        """总收益率"""
        return self.profit / self.initial_capital
    
    def can_buy(self, ts_code: str, price: float) -> bool:
        """判断是否可以买入"""
        # 检查持仓数量
        if len(self.positions) >= self.max_positions and ts_code not in self.positions:
            return False
        
        # 检查仓位上限
        max_buy_value = self.total_value * self.single_position_pct
        available_cash = min(
            self.cash,
            self.total_value * self.max_total_position_pct - self.position_value
        )
        
        return available_cash > 0
    
    def buy(self, ts_code: str, shares: int, price: float, trade_date: date) -> bool:
        """买入股票
        
        Args:
            ts_code: 股票代码
            shares: 股数（手*100）
            price: 买入价格
            trade_date: 交易日期
            
        Returns:
            是否成功
        """
        amount = shares * price
        
        if amount > self.cash:
            return False
        
        # 更新现金
        self.cash -= amount
        
        # 更新持仓
        if ts_code in self.positions:
            pos = self.positions[ts_code]
            total_cost = pos.cost_price * pos.shares + amount
            total_shares = pos.shares + shares
            pos.cost_price = total_cost / total_shares
            pos.shares = total_shares
        else:
            self.positions[ts_code] = Position(
                ts_code=ts_code,
                shares=shares,
                cost_price=price
            )
        
        # 记录交易
        self.trades.append({
            'date': trade_date,
            'ts_code': ts_code,
            'action': 'buy',
            'shares': shares,
            'price': price,
            'amount': amount
        })
        
        return True
    
    def sell(self, ts_code: str, shares: int, price: float, trade_date: date) -> bool:
        """卖出股票"""
        if ts_code not in self.positions:
            return False
        
        pos = self.positions[ts_code]
        if shares > pos.shares:
            shares = pos.shares  # 全部卖出
        
        amount = shares * price
        self.cash += amount
        
        # 更新持仓
        pos.shares -= shares
        if pos.shares == 0:
            del self.positions[ts_code]
        
        # 记录交易
        self.trades.append({
            'date': trade_date,
            'ts_code': ts_code,
            'action': 'sell',
            'shares': shares,
            'price': price,
            'amount': amount
        })
        
        return True
    
    def update_prices(self, prices: Dict[str, float]):
        """更新持仓价格"""
        for ts_code, price in prices.items():
            if ts_code in self.positions:
                self.positions[ts_code].current_price = price
    
    def record(self, trade_date: date):
        """记录每日净值"""
        self.history.append({
            'date': trade_date,
            'total_value': self.total_value,
            'cash': self.cash,
            'position_value': self.position_value,
            'position_pct': self.position_pct,
            'profit_pct': self.profit_pct,
            'positions': len(self.positions)
        })
    
    def get_history_df(self) -> pd.DataFrame:
        """获取历史净值DataFrame"""
        return pd.DataFrame(self.history)