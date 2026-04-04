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


class OrderMatcher:
    """订单撮合器"""
    
    def __init__(
        self,
        slippage: float = 0.001,  # 滑点0.1%
        commission: float = 0.0003  # 佣金0.03%
    ):
        self.slippage = slippage
        self.commission = commission
    
    def match(
        self,
        orders: List[Order],
        next_prices: Dict[str, float]
    ) -> List[Order]:
        """撮合订单（次日开盘价成交）
        
        Args:
            orders: 订单列表
            next_prices: 次日开盘价 {ts_code: price}
            
        Returns:
            撮合后的订单列表
        """
        for order in orders:
            if order.ts_code in next_prices:
                base_price = next_prices[order.ts_code]
                
                # 计算滑点
                if order.direction == 'buy':
                    order.fill_price = base_price * (1 + self.slippage)
                else:
                    order.fill_price = base_price * (1 - self.slippage)
                
                order.filled = True
        
        return orders
    
    def calculate_commission(self, amount: float) -> float:
        """计算佣金（最低5元）"""
        return max(amount * self.commission, 5.0)
    
    def get_total_cost(self, order: Order) -> Dict[str, float]:
        """获取订单总成本
        
        Returns:
            {amount: 成交金额, commission: 佣金, total: 总成本}
        """
        if not order.filled:
            return {'amount': 0, 'commission': 0, 'total': 0}
        
        amount = order.shares * order.fill_price
        commission = self.calculate_commission(amount)
        
        return {
            'amount': amount,
            'commission': commission,
            'total': amount + commission
        }