# -*- coding: utf-8 -*-
"""订单撮合"""

from typing import List, Dict
from dataclasses import dataclass
from datetime import date


@dataclass
class Order:
    ts_code: str
    direction: str
    shares: int
    order_date: date
    filled: bool = False
    fill_price: float = 0.0


class OrderMatcher:
    """订单撮合器"""
    
    def __init__(self, slippage: float = 0.0, commission: float = 0.0003):
        self.slippage = slippage
        self.commission = commission
    
    def match(self, orders: List[Order], prices: Dict[str, float]) -> List[Order]:
        for order in orders:
            if order.ts_code in prices:
                base_price = prices[order.ts_code]
                
                if order.direction == 'buy':
                    order.fill_price = base_price * (1 + self.slippage)
                else:
                    order.fill_price = base_price * (1 - self.slippage)
                
                order.filled = True
        
        return orders
    
    def calc_commission(self, amount: float) -> float:
        return max(amount * self.commission, 5.0)