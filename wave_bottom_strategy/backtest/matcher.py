# -*- coding: utf-8 -*-
"""订单撮合"""

from typing import List, Dict
from dataclasses import dataclass, field
from datetime import date
import pandas as pd

from utils.logger import get_logger

logger = get_logger('order_matcher')


@dataclass
class Order:
    """订单"""
    ts_code: str           # 股票代码
    direction: str         # 方向: buy/sell
    shares: int            # 股数
    order_date: date       # 下单日期
    
    # 成交信息（撮合后填充）
    filled: bool = False
    fill_price: float = 0.0
    fill_date: date = None
    commission: float = 0.0
    slippage: float = 0.0


class OrderMatcher:
    """订单撮合器
    
    模拟真实交易：次日开盘价成交、滑点、佣金
    """
    
    def __init__(
        self,
        slippage_rate: float = 0.001,  # 滑点率 0.1%
        commission_rate: float = 0.0003,  # 佣金率 0.03%
        min_commission: float = 5.0,  # 最低佣金
        stamp_duty_rate: float = 0.001  # 印花税率 0.1%（仅卖出）
    ):
        self.slippage_rate = slippage_rate
        self.commission_rate = commission_rate
        self.min_commission = min_commission
        self.stamp_duty_rate = stamp_duty_rate
    
    def match(
        self,
        orders: List[Order],
        next_day_prices: Dict[str, float],
        fill_date: date
    ) -> List[Order]:
        """撮合订单（次日开盘价成交）
        
        Args:
            orders: 订单列表
            next_day_prices: 次日开盘价 {ts_code: price}
            fill_date: 成交日期
            
        Returns:
            撮合后的订单列表
        """
        matched_orders = []
        
        for order in orders:
            if order.ts_code not in next_day_prices:
                logger.warning(f"无法撮合: {order.ts_code} 无价格数据")
                order.filled = False
                matched_orders.append(order)
                continue
            
            # 获取成交价格
            base_price = next_day_prices[order.ts_code]
            
            # 计算滑点
            if order.direction == 'buy':
                # 买入：价格上浮
                fill_price = base_price * (1 + self.slippage_rate)
            else:
                # 卖出：价格下浮
                fill_price = base_price * (1 - self.slippage_rate)
            
            # 计算佣金
            amount = order.shares * fill_price
            commission = max(amount * self.commission_rate, self.min_commission)
            
            # 卖出加印花税
            if order.direction == 'sell':
                commission += amount * self.stamp_duty_rate
            
            # 更新订单
            order.filled = True
            order.fill_price = fill_price
            order.fill_date = fill_date
            order.commission = commission
            order.slippage = abs(fill_price - base_price) * order.shares
            
            matched_orders.append(order)
            
            logger.debug(
                f"撮合成功: {order.direction} {order.ts_code} "
                f"{order.shares}股 @ {fill_price:.2f}, 佣金{commission:.2f}"
            )
        
        return matched_orders
    
    def calculate_commission(
        self,
        amount: float,
        is_sell: bool = False
    ) -> float:
        """计算交易成本
        
        Args:
            amount: 成交金额
            is_sell: 是否卖出
            
        Returns:
            交易成本
        """
        commission = max(amount * self.commission_rate, self.min_commission)
        
        if is_sell:
            commission += amount * self.stamp_duty_rate
        
        return commission
    
    def batch_match(
        self,
        order_list: List[Order],
        price_data: pd.DataFrame,
        trade_dates: List[date]
    ) -> List[Order]:
        """批量撮合订单
        
        Args:
            order_list: 订单列表
            price_data: 价格数据（含trade_date, ts_code, open列）
            trade_dates: 交易日列表
            
        Returns:
            撮合后的订单列表
        """
        results = []
        
        for order in order_list:
            # 找到下单日的下一个交易日
            try:
                order_idx = trade_dates.index(order.order_date)
                if order_idx + 1 >= len(trade_dates):
                    order.filled = False
                    results.append(order)
                    continue
                
                fill_date = trade_dates[order_idx + 1]
                
                # 获取次日开盘价
                mask = (
                    (price_data['trade_date'] == fill_date) &
                    (price_data['ts_code'] == order.ts_code)
                )
                
                if mask.sum() == 0:
                    order.filled = False
                    results.append(order)
                    continue
                
                next_open = price_data.loc[mask, 'open'].iloc[0]
                
                # 撮合
                matched = self.match(
                    [order],
                    {order.ts_code: next_open},
                    fill_date
                )
                results.extend(matched)
                
            except Exception as e:
                logger.error(f"批量撮合失败: {order.ts_code}, {e}")
                order.filled = False
                results.append(order)
        
        return results