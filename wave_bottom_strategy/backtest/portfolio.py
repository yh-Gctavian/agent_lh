# -*- coding: utf-8 -*-
"""组合管理 - 仓位管理、费用计算、持仓跟踪"""

from typing import Dict, List, Optional, Literal, Tuple
from dataclasses import dataclass, field
from datetime import date
import pandas as pd
import numpy as np

from wave_bottom_strategy.utils.logger import get_logger

logger = get_logger('portfolio')


@dataclass
class Position:
    """持仓信息"""
    ts_code: str
    shares: int
    cost_price: float
    current_price: float = 0.0
    buy_date: date = None
    hold_days: int = 0
    
    @property
    def market_value(self) -> float:
        """市值"""
        return self.shares * self.current_price
    
    @property
    def profit(self) -> float:
        """浮动盈亏"""
        return (self.current_price - self.cost_price) * self.shares
    
    @property
    def profit_pct(self) -> float:
        """盈亏比例"""
        if self.cost_price == 0:
            return 0
        return (self.current_price - self.cost_price) / self.cost_price
    
    @property
    def cost_amount(self) -> float:
        """持仓成本"""
        return self.shares * self.cost_price
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'ts_code': self.ts_code,
            'shares': self.shares,
            'cost_price': self.cost_price,
            'current_price': self.current_price,
            'market_value': self.market_value,
            'profit': self.profit,
            'profit_pct': self.profit_pct,
            'buy_date': self.buy_date,
            'hold_days': self.hold_days
        }


@dataclass
class TradeRecord:
    """交易记录"""
    trade_date: date
    ts_code: str
    direction: str  # 'buy' or 'sell'
    shares: int
    price: float
    amount: float
    commission: float
    stamp_duty: float
    transfer_fee: float
    slippage_cost: float
    total_cost: float  # 总交易成本
    
    def to_dict(self) -> dict:
        return {
            'trade_date': self.trade_date,
            'ts_code': self.ts_code,
            'direction': self.direction,
            'shares': self.shares,
            'price': self.price,
            'amount': self.amount,
            'commission': self.commission,
            'stamp_duty': self.stamp_duty,
            'transfer_fee': self.transfer_fee,
            'slippage_cost': self.slippage_cost,
            'total_cost': self.total_cost
        }


class FeeCalculator:
    """交易费用计算器"""
    
    def __init__(
        self,
        commission_rate: float = 0.0003,
        min_commission: float = 5.0,
        stamp_duty_rate: float = 0.001,
        transfer_fee_rate: float = 0.00001,
        slippage_rate: float = 0.001
    ):
        self.commission_rate = commission_rate
        self.min_commission = min_commission
        self.stamp_duty_rate = stamp_duty_rate  # 仅卖出
        self.transfer_fee_rate = transfer_fee_rate
        self.slippage_rate = slippage_rate
    
    def calc_buy_cost(self, shares: int, price: float) -> dict:
        """计算买入成本"""
        amount = shares * price
        commission = max(amount * self.commission_rate, self.min_commission)
        transfer_fee = amount * self.transfer_fee_rate
        fill_price = price * (1 + self.slippage_rate)
        slippage_cost = shares * (fill_price - price)
        total_amount = shares * fill_price + commission + transfer_fee
        
        return {
            'amount': amount,
            'fill_price': fill_price,
            'commission': commission,
            'stamp_duty': 0,
            'transfer_fee': transfer_fee,
            'slippage_cost': slippage_cost,
            'total_cost': total_amount
        }
    
    def calc_sell_cost(self, shares: int, price: float) -> dict:
        """计算卖出成本"""
        amount = shares * price
        commission = max(amount * self.commission_rate, self.min_commission)
        stamp_duty = amount * self.stamp_duty_rate
        transfer_fee = amount * self.transfer_fee_rate
        fill_price = price * (1 - self.slippage_rate)
        slippage_cost = shares * (price - fill_price)
        total_amount = shares * fill_price - commission - stamp_duty - transfer_fee
        
        return {
            'amount': amount,
            'fill_price': fill_price,
            'commission': commission,
            'stamp_duty': stamp_duty,
            'transfer_fee': transfer_fee,
            'slippage_cost': slippage_cost,
            'total_cost': total_amount
        }


class PositionSizer:
    """仓位管理器"""
    
    def __init__(
        self,
        mode: Literal['equal', 'score_weighted'] = 'equal',
        max_positions: int = 10,
        position_size: float = 0.1
    ):
        self.mode = mode
        self.max_positions = max_positions
        self.position_size = position_size
    
    def calc_position_sizes(
        self,
        total_capital: float,
        scores: pd.DataFrame,
        current_positions: Dict[str, Position] = None
    ) -> Dict[str, float]:
        """计算各股票的目标仓位金额"""
        if scores.empty:
            return {}
        
        available_capital = total_capital
        if current_positions:
            used_capital = sum(p.market_value for p in current_positions.values())
            available_capital = total_capital - used_capital
        
        if self.mode == 'equal':
            return self._equal_weight(available_capital, scores)
        else:
            return self._score_weighted(available_capital, scores)
    
    def _equal_weight(self, capital: float, scores: pd.DataFrame) -> Dict[str, float]:
        """等权分配"""
        n = min(len(scores), self.max_positions)
        position_amount = capital * self.position_size
        
        result = {}
        for i, row in scores.head(n).iterrows():
            if 'ts_code' in scores.columns:
                result[row['ts_code']] = position_amount
        
        return result
    
    def _score_weighted(self, capital: float, scores: pd.DataFrame) -> Dict[str, float]:
        """按分数加权分配"""
        n = min(len(scores), self.max_positions)
        top_scores = scores.head(n)
        
        total_score = top_scores['total_score'].sum() if 'total_score' in top_scores.columns else 0
        if total_score == 0:
            return self._equal_weight(capital, scores)
        
        result = {}
        for _, row in top_scores.iterrows():
            weight = row['total_score'] / total_score
            result[row['ts_code']] = capital * weight
        
        return result
    
    def calc_shares(self, amount: float, price: float) -> int:
        """计算可买股数"""
        shares = int(amount / price / 100) * 100
        return shares


class Portfolio:
    """组合管理"""
    
    def __init__(
        self,
        initial_capital: float,
        fee_calculator: FeeCalculator = None,
        position_sizer: PositionSizer = None
    ):
        self.initial_capital = initial_capital
        self.cash = initial_capital
        self.positions: Dict[str, Position] = {}
        
        self.fee_calculator = fee_calculator or FeeCalculator()
        self.position_sizer = position_sizer or PositionSizer()
        
        self.trade_records: List[TradeRecord] = []
        self.daily_values: List[dict] = []
    
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
            return 0
        return self.total_profit / self.initial_capital
    
    @property
    def position_count(self) -> int:
        """持仓数量"""
        return len(self.positions)
    
    def buy(
        self,
        ts_code: str,
        shares: int,
        price: float,
        trade_date: date
    ) -> Tuple[bool, Optional[TradeRecord]]:
        """买入"""
        cost_info = self.fee_calculator.calc_buy_cost(shares, price)
        total_cost = cost_info['total_cost']
        
        if total_cost > self.cash:
            logger.warning(f"资金不足: 需要{total_cost:.2f}, 可用{self.cash:.2f}")
            return False, None
        
        self.cash -= total_cost
        
        fill_price = cost_info['fill_price']
        if ts_code in self.positions:
            pos = self.positions[ts_code]
            total_cost_amount = pos.cost_price * pos.shares + shares * fill_price
            total_shares = pos.shares + shares
            pos.cost_price = total_cost_amount / total_shares
            pos.shares = total_shares
            pos.current_price = price
        else:
            self.positions[ts_code] = Position(
                ts_code=ts_code,
                shares=shares,
                cost_price=fill_price,
                current_price=price,
                buy_date=trade_date,
                hold_days=0
            )
        
        record = TradeRecord(
            trade_date=trade_date,
            ts_code=ts_code,
            direction='buy',
            shares=shares,
            price=price,
            amount=cost_info['amount'],
            commission=cost_info['commission'],
            stamp_duty=cost_info['stamp_duty'],
            transfer_fee=cost_info['transfer_fee'],
            slippage_cost=cost_info['slippage_cost'],
            total_cost=total_cost
        )
        self.trade_records.append(record)
        
        logger.info(f"买入 {ts_code}: {shares}股 @ {price:.2f}, 成本{total_cost:.2f}")
        return True, record
    
    def sell(
        self,
        ts_code: str,
        shares: int,
        price: float,
        trade_date: date
    ) -> Tuple[bool, Optional[TradeRecord]]:
        """卖出"""
        if ts_code not in self.positions:
            logger.warning(f"无持仓: {ts_code}")
            return False, None
        
        pos = self.positions[ts_code]
        actual_shares = min(shares, pos.shares)
        
        cost_info = self.fee_calculator.calc_sell_cost(actual_shares, price)
        total_amount = cost_info['total_cost']
        
        self.cash += total_amount
        
        pos.shares -= actual_shares
        if pos.shares == 0:
            del self.positions[ts_code]
        
        record = TradeRecord(
            trade_date=trade_date,
            ts_code=ts_code,
            direction='sell',
            shares=actual_shares,
            price=price,
            amount=cost_info['amount'],
            commission=cost_info['commission'],
            stamp_duty=cost_info['stamp_duty'],
            transfer_fee=cost_info['transfer_fee'],
            slippage_cost=cost_info['slippage_cost'],
            total_cost=total_amount
        )
        self.trade_records.append(record)
        
        logger.info(f"卖出 {ts_code}: {actual_shares}股 @ {price:.2f}, 所得{total_amount:.2f}")
        return True, record
    
    def update_prices(self, prices: Dict[str, float]):
        """更新持仓价格"""
        for ts_code, price in prices.items():
            if ts_code in self.positions:
                self.positions[ts_code].current_price = price
    
    def update_holding_days(self):
        """更新持仓天数"""
        for pos in self.positions.values():
            pos.hold_days += 1
    
    def record_daily(self, trade_date: date):
        """记录每日资产"""
        self.daily_values.append({
            'date': trade_date,
            'total_value': self.total_value,
            'cash': self.cash,
            'position_value': self.total_value - self.cash,
            'position_count': self.position_count,
            'profit': self.total_profit,
            'profit_pct': self.total_profit_pct
        })
    
    def get_position(self, ts_code: str) -> Optional[Position]:
        """获取指定持仓"""
        return self.positions.get(ts_code)
    
    def get_all_positions(self) -> List[Position]:
        """获取所有持仓"""
        return list(self.positions.values())
    
    def get_trade_records(self) -> pd.DataFrame:
        """获取交易记录"""
        if not self.trade_records:
            return pd.DataFrame()
        return pd.DataFrame([r.to_dict() for r in self.trade_records])
    
    def get_daily_values(self) -> pd.DataFrame:
        """获取每日资产"""
        if not self.daily_values:
            return pd.DataFrame()
        return pd.DataFrame(self.daily_values)
    
    def get_summary(self) -> dict:
        """获取组合摘要"""
        return {
            'initial_capital': self.initial_capital,
            'total_value': self.total_value,
            'cash': self.cash,
            'position_value': self.total_value - self.cash,
            'position_count': self.position_count,
            'total_profit': self.total_profit,
            'total_profit_pct': self.total_profit_pct,
            'trade_count': len(self.trade_records)
        }