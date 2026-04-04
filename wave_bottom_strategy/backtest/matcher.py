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


class OrderMatcher:
    """订单撮合器"""
    
    def __init__(self, slippage: float = 0.001, commission: float = 0.0003):
        self.slippage = slippage
        self.commission = commission
    
    def match(self, orders: List[Order], prices: Dict[str, float]) -> List[Order]:
        """撮合订单"""
        for order in orders:
            if order.ts_code in prices:
                base_price = prices[order.ts_code]
                
                # 滑点
                if order.direction == 'buy':
                    order.fill_price = base_price * (1 + self.slippage)
                else:
                    order.fill_price = base_price * (1 - self.slippage)
                
                order.filled = True
        
        return orders
    
    def calc_commission(self, amount: float) -> float:
        """计算佣金"""
        return max(amount * self.commission, 5.0)