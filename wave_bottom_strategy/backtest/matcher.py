# -*- coding: utf-8 -*-
"""订单撮合 - 次日开盘价成交、停牌处理"""

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from datetime import date
from enum import Enum
import pandas as pd

from data.loader import DataLoader
from utils.logger import get_logger

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
    - 处理涨跌停（可能无法成交）
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
        
        # 待处理订单队列
        self.pending_orders: List[Order] = []
        
        # 已处理订单
        self.processed_orders: List[Order] = []
    
    def create_order(
        self,
        ts_code: str,
        direction: str,
        shares: int,
        order_date: date,
        target_price: float = 0.0
    ) -> Order:
        """创建订单
        
        Args:
            ts_code: 股票代码
            direction: 方向 'buy' or 'sell'
            shares: 股数
            order_date: 下单日期
            target_price: 目标价格（0表示市价）
            
        Returns:
            订单对象
        """
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
        """处理待成交订单（次日开盘价成交）
        
        Args:
            trade_date: 交易日期
            suspended_stocks: 停牌股票列表
            
        Returns:
            (成交订单列表, 取消订单列表)
        """
        suspended_stocks = suspended_stocks or []
        filled_orders = []
        cancelled_orders = []
        
        for order in self.pending_orders:
            # 检查是否停牌
            if order.ts_code in suspended_stocks:
                order.status = OrderStatus.CANCELLED
                order.cancel_reason = '停牌'
                cancelled_orders.append(order)
                logger.warning(f"订单取消（停牌）: {order.ts_code}")
                continue
            
            # 获取开盘价
            fill_price = self._get_open_price(order.ts_code, trade_date)
            
            if fill_price is None or fill_price <= 0:
                order.status = OrderStatus.CANCELLED
                order.cancel_reason = '无法获取价格'
                cancelled_orders.append(order)
                logger.warning(f"订单取消（无价格）: {order.ts_code}")
                continue
            
            # 计算滑点
            if order.direction == 'buy':
                actual_price = fill_price * (1 + self.slippage)
            else:
                actual_price = fill_price * (1 - self.slippage)
            
            # 更新订单状态
            order.status = OrderStatus.FILLED
            order.fill_date = trade_date
            order.fill_price = actual_price
            order.fill_shares = order.shares
            
            # 计算费用
            self._calc_fees(order)
            
            filled_orders.append(order)
            logger.info(f"订单成交: {order.direction} {order.ts_code} {order.shares}股 @ {actual_price:.2f}")
        
        # 清空待处理队列
        self.pending_orders = [o for o in self.pending_orders if o.status == OrderStatus.PENDING]
        
        # 保存已处理订单
        self.processed_orders.extend(filled_orders)
        self.processed_orders.extend(cancelled_orders)
        
        return filled_orders, cancelled_orders
    
    def _get_open_price(self, ts_code: str, trade_date: date) -> Optional[float]:
        """获取开盘价
        
        Args:
            ts_code: 股票代码
            trade_date: 交易日期
            
        Returns:
            开盘价，无法获取返回None
        """
        try:
            # 转换日期格式
            date_str = str(trade_date).replace('-', '')
            symbol = ts_code.split('.')[0]
            
            # 加载日线数据
            df = self.data_loader.load_daily_data(symbol, date_str, date_str)
            
            if df.empty:
                return None
            
            # 返回开盘价
            open_price = df['open'].iloc[0]
            return float(open_price) if open_price > 0 else None
            
        except Exception as e:
            logger.error(f"获取开盘价失败: {ts_code} {trade_date}, {e}")
            return None
    
    def _calc_fees(self, order: Order):
        """计算交易费用"""
        amount = order.fill_shares * order.fill_price
        
        # 佣金
        order.commission = max(amount * self.commission_rate, self.min_commission)
        
        # 印花税（仅卖出）
        if order.direction == 'sell':
            order.stamp_duty = amount * self.stamp_duty_rate
        
        # 过户费
        order.transfer_fee = amount * self.transfer_fee_rate
        
        # 滑点成本
        base_price = order.fill_price / (1 + self.slippage) if order.direction == 'buy' else order.fill_price / (1 - self.slippage)
        order.slippage_cost = abs(order.fill_price - base_price) * order.fill_shares
        
        # 总金额
        if order.direction == 'buy':
            order.total_amount = amount + order.commission + order.transfer_fee
        else:
            order.total_amount = amount - order.commission - order.stamp_duty - order.transfer_fee
    
    def get_pending_orders(self) -> List[Order]:
        """获取待处理订单"""
        return self.pending_orders.copy()
    
    def get_processed_orders(self, start_date: date = None, end_date: date = None) -> pd.DataFrame:
        """获取已处理订单记录"""
        if not self.processed_orders:
            return pd.DataFrame()
        
        df = pd.DataFrame([o.to_dict() for o in self.processed_orders])
        
        if start_date:
            df = df[df['fill_date'] >= start_date]
        if end_date:
            df = df[df['fill_date'] <= end_date]
        
        return df
    
    def clear_pending(self):
        """清空待处理订单"""
        self.pending_orders = []
    
    def get_order_stats(self) -> dict:
        """获取订单统计"""
        total = len(self.processed_orders)
        filled = sum(1 for o in self.processed_orders if o.status == OrderStatus.FILLED)
        cancelled = sum(1 for o in self.processed_orders if o.status == OrderStatus.CANCELLED)
        
        buy_orders = [o for o in self.processed_orders if o.direction == 'buy' and o.status == OrderStatus.FILLED]
        sell_orders = [o for o in self.processed_orders if o.direction == 'sell' and o.status == OrderStatus.FILLED]
        
        total_buy_amount = sum(o.total_amount for o in buy_orders)
        total_sell_amount = sum(o.total_amount for o in sell_orders)
        
        total_commission = sum(o.commission for o in self.processed_orders if o.status == OrderStatus.FILLED)
        total_stamp_duty = sum(o.stamp_duty for o in self.processed_orders if o.status == OrderStatus.FILLED)
        total_transfer_fee = sum(o.transfer_fee for o in self.processed_orders if o.status == OrderStatus.FILLED)
        
        return {
            'total_orders': total,
            'filled_orders': filled,
            'cancelled_orders': cancelled,
            'fill_rate': filled / total if total > 0 else 0,
            'buy_orders': len(buy_orders),
            'sell_orders': len(sell_orders),
            'total_buy_amount': total_buy_amount,
            'total_sell_amount': total_sell_amount,
            'total_commission': total_commission,
            'total_stamp_duty': total_stamp_duty,
            'total_transfer_fee': total_transfer_fee,
            'total_fees': total_commission + total_stamp_duty + total_transfer_fee
        }