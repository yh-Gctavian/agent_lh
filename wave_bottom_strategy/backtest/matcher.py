# -*- coding: utf-8 -*-
"""订单撮合"""

from typing import List, Dict
from dataclasses import dataclass
from datetime import date


@dataclass
class Order:
    """订单"""
    ts_code: str
    direction: str  # buy/sell
    shares: int
    order_date: date
    filled: bool = False
    fill_price: float = 0.0
    fill_date: date = None
    commission: float = 0.0


class OrderMatcher:
    """订单撮合器
    
    费用规则：
    - 买入佣金：0.03%
    - 卖出佣金：0.13%（含印花税0.1%）
    - 滑点：0.1%
    """
    
    def __init__(
        self,
        buy_commission: float = 0.0003,  # 买入0.03%
        sell_commission: float = 0.0013,  # 卖出0.13%
        slippage: float = 0.001  # 滑点0.1%
    ):
        self.buy_commission = buy_commission
        self.sell_commission = sell_commission
        self.slippage = slippage
    
    def match(
        self,
        orders: List[Order],
        next_day_prices: Dict[str, float],
        next_day: date
    ) -> List[Order]:
        """撮合订单（次日开盘价成交）
        
        Args:
            orders: 订单列表
            next_day_prices: 次日开盘价
            next_day: 次日日期
            
        Returns:
            撮合后的订单列表
        """
        for order in orders:
            if order.ts_code not in next_day_prices:
                continue  # 无法成交
            
            base_price = next_day_prices[order.ts_code]
            
            # 应用滑点
            if order.direction == 'buy':
                fill_price = base_price * (1 + self.slippage)
                order.commission = order.shares * fill_price * self.buy_commission
            else:
                fill_price = base_price * (1 - self.slippage)
                order.commission = order.shares * fill_price * self.sell_commission
            
            order.fill_price = fill_price
            order.fill_date = next_day
            order.filled = True
        
        return orders
    
    def calculate_commission(self, amount: float, direction: str) -> float:
        """计算佣金"""
        rate = self.buy_commission if direction == 'buy' else self.sell_commission
        return max(amount * rate, 5.0)  # 最低5元