# -*- coding: utf-8 -*-
"""订单撮合 - 次日开盘价成交、停牌处理"""

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from datetime import date
from enum import Enum
import pandas as pd

from wave_bottom_strategy.data.loader import DataLoader
from wave_bottom_strategy.utils.logger import get_logger

logger = get_logger('order_matcher')


class OrderStatus(Enum):
    """订单状态"""
    PENDING = 'pending'  # 待成交
    FILLED = 'filled'  # 已成交
    CANCELLED = 'cancelled'  # 已取消（停牌等）
    PARTIAL = 'partial'  # 部分成交


class OrderDirection(Enum):
    """订单方向"""
    BUY = 'buy'
    SELL = 'sell'


@dataclass
class Order:
    """订单"""
    ts_code: str
    direction: str  # 'buy' or 'sell'
    shares: int
    order_date: date  # 下单日期（T日）
    target_price: float = 0.0  # 目标价格（0表示市价）
    
    # 成交信息
    status: OrderStatus = OrderStatus.PENDING
    fill_date: date = None  # 成交日期
    fill_price: float = 0.0  # 成交价格
    fill_shares: int = 0  # 成交股数
    
    # 费用信息
    commission: float = 0.0
    stamp_duty: float = 0.0
    transfer_fee: float = 0.0
    slippage_cost: float = 0.0
    total_amount: float = 0.0
    
    # 取消原因
    cancel_reason: str = ''
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'ts_code': self.ts_code,
            'direction': self.direction,
            'shares': self.shares,
            'order_date': self.order_date,
            'target_price': self.target_price,
            'status': self.status.value,
            'fill_date': self.fill_date,
            'fill_price': self.fill_price,
            'fill_shares': self.fill_shares,
            'commission': self.commission,
            'stamp_duty': self.stamp_duty,
            'transfer_fee': self.transfer_fee,
            'slippage_cost': self.slippage_cost,
            'total_amount': self.total_amount,
            'cancel_reason': self.cancel_reason
        }


class OrderMatcher:
    """订单撮合器
    
    实现次日开盘价成交机制：
    - T日信号触发 -> T+1日开盘价成交
    - 处理停牌股票（无法成交）
    """
    
    def __init__(
        self,
        data_loader: DataLoader = None,
        slippage: float = 0.001,
        commission_rate: float = 0.0003,
        min_commission: float = 5.0,
        stamp_duty_rate: float = 0.001,
        transfer_fee_rate: float = 0.00001
    ):
        self.data_loader = data_loader or DataLoader()
        self.slippage = slippage
        self.commission_rate = commission_rate
        self.min_commission = min_commission
        self.stamp_duty_rate = stamp_duty_rate
        self.transfer_fee_rate = transfer_fee_rate
        
        self.pending_orders: List[Order] = []
        self.processed_orders: List[Order] = []
    
    def create_order(
        self,
        ts_code: str,
        direction: str,
        shares: int,
        order_date: date,
        target_price: float = 0.0
    ) -> Order:
        """创建订单"""
        order = Order(
            ts_code=ts_code,
            direction=direction,
            shares=shares,
            order_date=order_date,
            target_price=target_price
        )
        
        self.pending_orders.append(order)
        logger.info(f"创建订单: {direction} {ts_code} {shares}股 @ {order_date}")
        
        return order
    
    def process_orders(
        self,
        trade_date: date,
        suspended_stocks: List[str] = None
    ) -> Tuple[List[Order], List[Order]]:
        """处理待成交订单（次日开盘价成交）"""
        suspended_stocks = suspended_stocks or []
        filled_orders = []
        cancelled_orders = []
        
        for order in self.pending_orders:
            if order.ts_code in suspended_stocks:
                order.status = OrderStatus.CANCELLED
                order.cancel_reason = '停牌'
                cancelled_orders.append(order)
                logger.warning(f"订单取消（停牌）: {order.ts_code}")
                continue
            
            fill_price = self._get_open_price(order.ts_code, trade_date)
            
            if fill_price is None or fill_price <= 0:
                order.status = OrderStatus.CANCELLED
                order.cancel_reason = '无法获取价格'
                cancelled_orders.append(order)
                logger.warning(f"订单取消（无价格）: {order.ts_code}")
                continue
            
            if order.direction == 'buy':
                actual_price = fill_price * (1 + self.slippage)
            else:
                actual_price = fill_price * (1 - self.slippage)
            
            order.status = OrderStatus.FILLED
            order.fill_date = trade_date
            order.fill_price = actual_price
            order.fill_shares = order.shares
            
            self._calc_fees(order)
            
            filled_orders.append(order)
            logger.info(f"订单成交: {order.direction} {order.ts_code} {order.shares}股 @ {actual_price:.2f}")
        
        self.pending_orders = [o for o in self.pending_orders if o.status == OrderStatus.PENDING]
        
        self.processed_orders.extend(filled_orders)
        self.processed_orders.extend(cancelled_orders)
        
        return filled_orders, cancelled_orders
    
    def _get_open_price(self, ts_code: str, trade_date: date) -> Optional[float]:
        """获取开盘价"""
        try:
            date_str = str(trade_date).replace('-', '')
            symbol = ts_code.split('.')[0]
            
            df = self.data_loader.load_daily_data(symbol, date_str, date_str)
            
            if df.empty:
                return None
            
            open_price = df['open'].iloc[0]
            return float(open_price) if open_price > 0 else None
            
        except Exception as e:
            logger.error(f"获取开盘价失败: {ts_code} {trade_date}, {e}")
            return None
    
    def _calc_fees(self, order: Order):
        """计算交易费用"""
        amount = order.fill_shares * order.fill_price
        
        order.commission = max(amount * self.commission_rate, self.min_commission)
        
        if order.direction == 'sell':
            order.stamp_duty = amount * self.stamp_duty_rate
        
        order.transfer_fee = amount * self.transfer_fee_rate
        
        if order.direction == 'buy':
            order.total_amount = amount + order.commission + order.transfer_fee
        else:
            order.total_amount = amount - order.commission - order.stamp_duty - order.transfer_fee
    
    def get_pending_orders(self) -> List[Order]:
        """获取待处理订单"""
        return self.pending_orders.copy()
    
    def clear_pending(self):
        """清空待处理订单"""
        self.pending_orders = []
    
    def get_order_stats(self) -> dict:
        """获取订单统计"""
        total = len(self.processed_orders)
        filled = sum(1 for o in self.processed_orders if o.status == OrderStatus.FILLED)
        
        return {
            'total_orders': total,
            'filled_orders': filled,
            'cancelled_orders': total - filled,
            'fill_rate': filled / total if total > 0 else 0
        }