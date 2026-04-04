# -*- coding: utf-8 -*-
"""组合管理"""

from typing import Dict, List
from dataclasses import dataclass, field
from datetime import date
import pandas as pd

from utils.logger import get_logger

logger = get_logger('portfolio')


@dataclass
class Position:
    """持仓信息"""
    ts_code: str          # 股票代码
    shares: int           # 持仓股数
    cost_price: float     # 成本价
    buy_date: date        # 买入日期
    
    current_price: float = 0.0  # 当前价
    market_value: float = 0.0   # 市值
    
    @property
    def profit(self) -> float:
        """持仓盈亏"""
        return (self.current_price - self.cost_price) * self.shares
    
    @property
    def profit_pct(self) -> float:
        """盈亏比例"""
        if self.cost_price == 0:
            return 0.0
        return (self.current_price - self.cost_price) / self.cost_price * 100


class Portfolio:
    """组合管理"""
    
    def __init__(self, initial_capital: float):
        self.initial_capital = initial_capital
        self.cash = initial_capital
        self.positions: Dict[str, Position] = {}
        self.history: List[Dict] = []
        self.trade_records: List[Dict] = []
    
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
        if self.initial_capital == 0:
            return 0.0
        return self.total_profit / self.initial_capital * 100
    
    @property
    def position_count(self) -> int:
        """持仓数量"""
        return len(self.positions)
    
    def buy(
        self,
        ts_code: str,
        shares: int,
        price: float,
        trade_date: date,
        commission: float = 0.0
    ) -> bool:
        """买入股票
        
        Args:
            ts_code: 股票代码
            shares: 买入股数
            price: 买入价格
            trade_date: 交易日期
            commission: 佣金
            
        Returns:
            是否成功
        """
        amount = shares * price + commission
        
        if amount > self.cash:
            logger.warning(f"资金不足: 需要{amount}, 可用{self.cash}")
            return False
        
        # 扣除资金
        self.cash -= amount
        
        # 更新持仓
        if ts_code in self.positions:
            # 加仓
            pos = self.positions[ts_code]
            total_shares = pos.shares + shares
            total_cost = pos.cost_price * pos.shares + price * shares
            pos.cost_price = total_cost / total_shares
            pos.shares = total_shares
        else:
            # 新建仓位
            self.positions[ts_code] = Position(
                ts_code=ts_code,
                shares=shares,
                cost_price=price,
                buy_date=trade_date,
                current_price=price,
                market_value=shares * price
            )
        
        # 记录交易
        self.trade_records.append({
            'date': trade_date,
            'action': 'buy',
            'ts_code': ts_code,
            'shares': shares,
            'price': price,
            'amount': amount,
            'commission': commission
        })
        
        logger.info(f"买入 {ts_code}: {shares}股 @ {price}, 金额{amount}")
        
        return True
    
    def sell(
        self,
        ts_code: str,
        shares: int,
        price: float,
        trade_date: date,
        commission: float = 0.0
    ) -> bool:
        """卖出股票
        
        Args:
            ts_code: 股票代码
            shares: 卖出股数
            price: 卖出价格
            trade_date: 交易日期
            commission: 佣金
            
        Returns:
            是否成功
        """
        if ts_code not in self.positions:
            logger.warning(f"无持仓: {ts_code}")
            return False
        
        pos = self.positions[ts_code]
        
        if shares > pos.shares:
            logger.warning(f"持仓不足: 需要{shares}, 拥有{pos.shares}")
            shares = pos.shares  # 全部卖出
        
        amount = shares * price - commission
        
        # 增加资金
        self.cash += amount
        
        # 更新持仓
        pos.shares -= shares
        pos.market_value = pos.shares * price
        
        if pos.shares == 0:
            # 清仓
            del self.positions[ts_code]
        
        # 记录交易
        self.trade_records.append({
            'date': trade_date,
            'action': 'sell',
            'ts_code': ts_code,
            'shares': shares,
            'price': price,
            'amount': amount,
            'commission': commission,
            'profit': (price - pos.cost_price) * shares
        })
        
        logger.info(f"卖出 {ts_code}: {shares}股 @ {price}, 金额{amount}")
        
        return True
    
    def update_prices(self, prices: Dict[str, float]):
        """更新持仓价格
        
        Args:
            prices: 股票代码 -> 当前价格
        """
        for ts_code, price in prices.items():
            if ts_code in self.positions:
                pos = self.positions[ts_code]
                pos.current_price = price
                pos.market_value = pos.shares * price
    
    def record(self, trade_date: date):
        """记录当日持仓快照
        
        Args:
            trade_date: 交易日期
        """
        self.history.append({
            'date': trade_date,
            'total_value': self.total_value,
            'cash': self.cash,
            'position_count': self.position_count,
            'profit_pct': self.total_profit_pct
        })
    
    def get_history_df(self) -> pd.DataFrame:
        """获取历史记录DataFrame"""
        return pd.DataFrame(self.history)
    
    def get_trade_records_df(self) -> pd.DataFrame:
        """获取交易记录DataFrame"""
        return pd.DataFrame(self.trade_records)
    
    def get_positions_df(self) -> pd.DataFrame:
        """获取持仓DataFrame"""
        if not self.positions:
            return pd.DataFrame()
        
        data = []
        for pos in self.positions.values():
            data.append({
                'ts_code': pos.ts_code,
                'shares': pos.shares,
                'cost_price': pos.cost_price,
                'current_price': pos.current_price,
                'market_value': pos.market_value,
                'profit': pos.profit,
                'profit_pct': pos.profit_pct,
                'buy_date': pos.buy_date
            })
        
        return pd.DataFrame(data)
    
    def clear_all(self, prices: Dict[str, float], trade_date: date):
        """清空所有持仓
        
        Args:
            prices: 当前价格字典
            trade_date: 交易日期
        """
        for ts_code in list(self.positions.keys()):
            price = prices.get(ts_code, self.positions[ts_code].current_price)
            self.sell(ts_code, self.positions[ts_code].shares, price, trade_date)