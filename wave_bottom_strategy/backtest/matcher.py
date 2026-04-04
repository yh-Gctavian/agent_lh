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
    """订单撮合器
    
    费用规则：
    - 买入费率：0.03%
    - 卖出费率：0.13%（含印花税0.1%）
    - 滑点：0.1%
    """
    
    def __init__(
        self,
        buy_commission: float = 0.0003,   # 买入佣金0.03%
        sell_commission: float = 0.0013,  # 卖出佣金0.13%（含印花税）
        slippage: float = 0.001,          # 滑点0.1%
        min_commission: float = 5.0       # 最低佣金5元
    ):
        self.buy_commission = buy_commission
        self.sell_commission = sell_commission
        self.slippage = slippage
        self.min_commission = min_commission
    
    def match(
        self,
        orders: List[Order],
        prices: Dict[str, float]
    ) -> List[Order]:
        """撮合订单（次日开盘价成交）
        
        Args:
            orders: 订单列表
            prices: 开盘价 {ts_code: price}
            
        Returns:
            撮合后的订单列表
        """
        for order in orders:
            if order.ts_code not in prices:
                order.filled = False
                continue
            
            base_price = prices[order.ts_code]
            
            # 应用滑点
            if order.direction == 'buy':
                # 买入：价格上浮
                fill_price = base_price * (1 + self.slippage)
            else:
                # 卖出：价格下浮
                fill_price = base_price * (1 - self.slippage)
            
            order.fill_price = fill_price
            order.filled = True
            order.fill_date = order.order_date  # 次日
        
        return orders
    
    def calculate_trade_cost(
        self,
        direction: str,
        amount: float
    ) -> Dict[str, float]:
        """计算交易成本
        
        Args:
            direction: 买卖方向
            amount: 成交金额
            
        Returns:
            费用明细
        """
        if direction == 'buy':
            commission = max(amount * self.buy_commission, self.min_commission)
            stamp_duty = 0
        else:
            commission = max(amount * self.sell_commission, self.min_commission)
            stamp_duty = amount * 0.001  # 印花税0.1%
        
        slippage_cost = amount * self.slippage
        
        return {
            'commission': commission,
            'stamp_duty': stamp_duty,
            'slippage': slippage_cost,
            'total_cost': commission + stamp_duty + slippage_cost
        }
    
    def get_executed_price(
        self,
        base_price: float,
        direction: str
    ) -> float:
        """获取实际成交价（含滑点）
        
        Args:
            base_price: 基准价格
            direction: 买卖方向
            
        Returns:
            成交价格
        """
        if direction == 'buy':
            return base_price * (1 + self.slippage)
        else:
            return base_price * (1 - self.slippage)