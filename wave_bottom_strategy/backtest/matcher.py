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
    
    # 成交信息
    filled: bool = False
    fill_price: float = 0.0
    fill_date: date = None


class OrderMatcher:
    """订单撮合器
    
    费用规则：
    - 买入佣金: 0.03%
    - 卖出佣金: 0.03% + 印花税 0.1% = 0.13%
    - 滑点: 0.1%
    """
    
    def __init__(
        self,
        buy_commission: float = 0.0003,   # 买入佣金 0.03%
        sell_commission: float = 0.0013,  # 卖出佣金+印花税 0.13%
        slippage: float = 0.001,          # 滑点 0.1%
        min_commission: float = 5.0       # 最低佣金
    ):
        self.buy_commission = buy_commission
        self.sell_commission = sell_commission
        self.slippage = slippage
        self.min_commission = min_commission
    
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
        for order in orders:
            ts_code = order.ts_code
            
            if ts_code not in next_day_prices:
                # 无法获取价格，订单失败
                order.filled = False
                continue
            
            base_price = next_day_prices[ts_code]
            
            # 计算滑点后价格
            if order.direction == 'buy':
                # 买入：价格上浮
                order.fill_price = base_price * (1 + self.slippage)
            else:
                # 卖出：价格下浮
                order.fill_price = base_price * (1 - self.slippage)
            
            order.filled = True
            order.fill_date = order.order_date  # 实际成交日期应为次日
        
        return orders
    
    def calculate_total_cost(self, order: Order) -> Dict[str, float]:
        """计算订单总成本
        
        Args:
            order: 已成交订单
            
        Returns:
            成本明细
        """
        if not order.filled:
            return {}
        
        amount = order.shares * order.fill_price
        
        if order.direction == 'buy':
            commission = max(amount * self.buy_commission, self.min_commission)
            slippage_cost = amount * self.slippage
            total_cost = amount + commission + slippage_cost
        else:
            commission = max(amount * self.sell_commission, self.min_commission)
            slippage_cost = amount * self.slippage
            total_cost = commission + slippage_cost  # 卖出时从收入中扣除
            total_cost = -total_cost  # 负数表示费用
        
        return {
            'amount': amount,
            'commission': commission if order.direction == 'buy' else -commission,
            'slippage': slippage_cost if order.direction == 'buy' else -slippage_cost,
            'total': total_cost if order.direction == 'buy' else amount + total_cost
        }
    
    def get_buy_amount(self, shares: int, price: float) -> float:
        """计算买入所需金额（含费用）
        
        Args:
            shares: 股数
            price: 价格
            
        Returns:
            总金额
        """
        amount = shares * price
        slippage_amount = amount * self.slippage
        commission = max(amount * self.buy_commission, self.min_commission)
        
        return amount + slippage_amount + commission
    
    def get_sell_amount(self, shares: int, price: float) -> float:
        """计算卖出所得金额（扣除费用）
        
        Args:
            shares: 股数
            price: 价格
            
        Returns:
            实得金额
        """
        amount = shares * price
        slippage_amount = amount * self.slippage
        commission = max(amount * self.sell_commission, self.min_commission)
        
        return amount - slippage_amount - commission