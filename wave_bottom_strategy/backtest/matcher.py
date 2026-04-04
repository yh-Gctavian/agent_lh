# -*- coding: utf-8 -*-
"""订单撮合"""

from typing import List, Dict
from dataclasses import dataclass
from datetime import date


@dataclass
class Order:
    """订单"""
    ts_code: str       # 股票代码
    direction: str     # 方向: buy/sell
    shares: int        # 股数
    order_date: date   # 下单日期
    
    # 成交信息（撮合后填充）
    filled: bool = False
    fill_price: float = 0.0
    fill_date: date = None


class OrderMatcher:
    """订单撮合器"""
    
    def __init__(self, slippage: float = 0.0, commission: float = 0.0003):
        self.slippage = slippage  # 滑点
        self.commission = commission  # 佣金率
    
    def match(
        self,
        orders: List[Order],
        next_day_prices: Dict[str, float]
    ) -> List[Order]:
        """撮合订单（次日开盘价成交）
        
        Args:
            orders: 订单列表
            next_day_prices: 次日开盘价 {ts_code: price}
            
        Returns:
            撮合后的订单列表
        """
        # TODO: 实现撮合逻辑
        raise NotImplementedError
    
    def calculate_commission(self, amount: float) -> float:
        """计算佣金
        
        Args:
            amount: 成交金额
            
        Returns:
            佣金金额
        """
        return max(amount * self.commission, 5.0)  # 最低5元