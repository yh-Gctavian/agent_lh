# -*- coding: utf-8 -*-
"""回测引擎"""

from typing import Dict, List, Optional
from datetime import datetime
import pandas as pd

from .portfolio import Portfolio
from .matcher import OrderMatcher, Order
from .benchmark import Benchmark
from selector.engine import SelectorEngine
from utils.logger import get_logger

logger = get_logger('backtest_engine')


class BacktestEngine:
    """回测引擎"""
    
    def __init__(
        self,
        initial_capital: float = 1_000_000,
        benchmark_code: str = "000300"
    ):
        self.initial_capital = initial_capital
        self.selector = SelectorEngine()
        self.portfolio = Portfolio(initial_capital)
        self.matcher = OrderMatcher()
        self.benchmark = Benchmark(benchmark_code)
    
    def run(
        self,
        stock_data: Dict[str, pd.DataFrame],
        start_date: str,
        end_date: str
    ) -> Dict:
        """运行回测
        
        Args:
            stock_data: {symbol: 日K线DataFrame}
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            回测结果
        """
        logger.info(f"开始回测: {start_date} -> {end_date}")
        
        # 加载基准
        self.benchmark.load_data(start_date, end_date)
        
        # 获取交易日列表
        trade_dates = self._get_trade_dates(stock_data)
        
        for i, trade_date in enumerate(trade_dates):
            # 更新持仓价格
            prices = self._get_prices(stock_data, trade_date)
            self.portfolio.update_prices(prices)
            
            # 执行选股
            result = self.selector.run(stock_data, trade_date)
            buy_list = self.selector.select_top(result, 10)
            
            # 生成订单
            orders = self._generate_orders(buy_list, prices, trade_date)
            
            # 次日撮合
            if i + 1 < len(trade_dates):
                next_date = trade_dates[i + 1]
                next_prices = self._get_prices(stock_data, next_date)
                orders = self.matcher.match(orders, next_prices, next_date)
                
                # 执行成交
                self._execute_orders(orders)
            
            # 记录净值
            self.portfolio.record(trade_date)
        
        # 计算绩效
        metrics = self._calculate_metrics()
        
        logger.info(f"回测完成: 收益率{metrics['total_return']:.2%}")
        
        return {
            'metrics': metrics,
            'history': self.portfolio.get_history_df(),
            'trades': pd.DataFrame(self.portfolio.trades)
        }
    
    def _get_trade_dates(self, stock_data: Dict) -> List[str]:
        """获取交易日列表"""
        all_dates = set()
        for data in stock_data.values():
            dates = data['trade_date'].tolist()
            all_dates.update(dates)
        return sorted(list(all_dates))
    
    def _get_prices(self, stock_data: Dict, trade_date: str) -> Dict[str, float]:
        """获取当日价格"""
        prices = {}
        for symbol, data in stock_data.items():
            row = data[data['trade_date'] == trade_date]
            if not row.empty:
                prices[symbol] = row['close'].iloc[0]
        return prices
    
    def _generate_orders(
        self,
        buy_list: List[str],
        prices: Dict[str, float],
        trade_date: str
    ) -> List[Order]:
        """生成买入订单"""
        orders = []
        
        for symbol in buy_list:
            if symbol not in prices:
                continue
            
            if self.portfolio.can_buy(symbol, prices[symbol]):
                # 计算买入股数（单票10%仓位）
                max_value = self.portfolio.total_value * 0.10
                shares = int(max_value / prices[symbol] / 100) * 100  # 整手
                
                if shares > 0:
                    orders.append(Order(
                        ts_code=symbol,
                        direction='buy',
                        shares=shares,
                        order_date=trade_date
                    ))
        
        return orders
    
    def _execute_orders(self, orders: List[Order]):
        """执行成交订单"""
        for order in orders:
            if not order.filled:
                continue
            
            if order.direction == 'buy':
                self.portfolio.buy(
                    order.ts_code,
                    order.shares,
                    order.fill_price,
                    order.fill_date
                )
                self.portfolio.cash -= order.commission
    
    def _calculate_metrics(self) -> Dict:
        """计算绩效指标"""
        history = self.portfolio.get_history_df()
        
        if history.empty:
            return {}
        
        # 收益率序列
        returns = history['total_value'].pct_change()
        
        # 年化收益
        total_return = history['profit_pct'].iloc[-1]
        days = len(history)
        annual_return = (1 + total_return) ** (252 / days) - 1
        
        # 最大回撤
        cummax = history['total_value'].cummax()
        drawdown = (history['total_value'] - cummax) / cummax
        max_drawdown = drawdown.min()
        
        # 夏普比率
        sharpe = returns.mean() / returns.std() * (252 ** 0.5) if returns.std() > 0 else 0
        
        # 胜率
        trades = pd.DataFrame(self.portfolio.trades)
        if not trades.empty:
            buy_trades = trades[trades['action'] == 'buy']
            sell_trades = trades[trades['action'] == 'sell']
            
            # 计算盈亏
            win_count = 0
            total_trade_count = 0
            
            for sell in sell_trades.to_dict('records'):
                # 找对应买入
                buy = buy_trades[buy_trades['ts_code'] == sell['ts_code']]
                if not buy.empty:
                    buy_price = buy['price'].iloc[-1]
                    if sell['price'] > buy_price:
                        win_count += 1
                    total_trade_count += 1
            
            win_rate = win_count / total_trade_count if total_trade_count > 0 else 0
        else:
            win_rate = 0
        
        return {
            'total_return': total_return,
            'annual_return': annual_return,
            'max_drawdown': max_drawdown,
            'sharpe_ratio': sharpe,
            'win_rate': win_rate,
            'trade_count': len(trades)
        }