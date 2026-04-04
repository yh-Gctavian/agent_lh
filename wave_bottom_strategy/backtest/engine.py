# -*- coding: utf-8 -*-
"""回测引擎"""

from typing import Dict, List, Optional
from datetime import date, timedelta
import pandas as pd
import numpy as np

from .portfolio import Portfolio
from .matcher import OrderMatcher, Order
from .benchmark import Benchmark
from selector.engine import SelectorEngine
from data.loader import DataLoader
from data.processor import DataProcessor
from utils.logger import get_logger

logger = get_logger('backtest_engine')


class BacktestEngine:
    """回测引擎"""
    
    def __init__(
        self,
        selector: SelectorEngine = None,
        initial_capital: float = 1_000_000.0,
        benchmark_code: str = "000300",
        max_positions: int = 10,
        position_size: float = 0.1,  # 单只股票仓位比例
        min_score: float = 70.0,
        sell_days: int = 5,  # 最大持仓天数
        stop_loss: float = -0.05,  # 止损比例
        take_profit: float = 0.15  # 止盈比例
    ):
        self.selector = selector or SelectorEngine()
        self.initial_capital = initial_capital
        self.max_positions = max_positions
        self.position_size = position_size
        self.min_score = min_score
        self.sell_days = sell_days
        self.stop_loss = stop_loss
        self.take_profit = take_profit
        
        # 初始化组件
        self.portfolio = Portfolio(initial_capital)
        self.matcher = OrderMatcher()
        self.benchmark = Benchmark(benchmark_code)
        self.data_loader = DataLoader()
        self.data_processor = DataProcessor()
        
        logger.info(f"回测引擎初始化: 初始资金{initial_capital}, 最大持仓{max_positions}")
    
    def run(
        self,
        start_date: str,
        end_date: str,
        stock_pool: List[str] = None
    ) -> Dict:
        """运行回测
        
        Args:
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
            stock_pool: 股票池
            
        Returns:
            回测结果
        """
        logger.info(f"开始回测: {start_date} -> {end_date}")
        
        # 1. 加载交易日历
        trade_dates = self._get_trade_dates(start_date, end_date)
        logger.info(f"交易日数: {len(trade_dates)}")
        
        # 2. 加载基准数据
        self.benchmark.load_data(
            start_date.replace('-', ''),
            end_date.replace('-', '')
        )
        
        # 3. 加载股票池
        if stock_pool is None:
            stock_pool = self.data_loader.load_stock_pool('hs300')
        
        # 4. 预加载股票数据
        stock_data = self._preload_stock_data(stock_pool, start_date, end_date)
        
        # 5. 主循环
        for i, trade_date in enumerate(trade_dates):
            self._daily_process(trade_date, trade_dates, i, stock_data, stock_pool)
            
            # 记录每日状态
            self.portfolio.record(trade_date)
        
        # 6. 汇总结果
        result = self._generate_result()
        
        logger.info("回测完成")
        
        return result
    
    def _get_trade_dates(self, start: str, end: str) -> List[date]:
        """获取交易日列表"""
        dates = self.data_loader.load_trade_calendar(
            start.replace('-', ''),
            end.replace('-', '')
        )
        
        if dates:
            return [pd.to_datetime(d).date() for d in dates]
        
        # 如果获取失败，生成简单日历
        start_dt = pd.to_datetime(start).date()
        end_dt = pd.to_datetime(end).date()
        
        dates = []
        current = start_dt
        while current <= end_dt:
            if current.weekday() < 5:  # 工作日
                dates.append(current)
            current += timedelta(days=1)
        
        return dates
    
    def _preload_stock_data(
        self,
        stock_pool: List[str],
        start_date: str,
        end_date: str
    ) -> Dict[str, pd.DataFrame]:
        """预加载股票数据"""
        logger.info(f"预加载股票数据: {len(stock_pool)}只")
        
        data = {}
        for symbol in stock_pool[:50]:  # 限制数量避免太慢
            try:
                df = self.data_loader.load_daily_data(
                    symbol=symbol,
                    start_date=start_date.replace('-', ''),
                    end_date=end_date.replace('-', ''),
                    adjust='qfq'
                )
                if not df.empty:
                    data[symbol] = df
            except Exception as e:
                logger.debug(f"{symbol} 加载失败: {e}")
        
        logger.info(f"成功加载: {len(data)}只")
        return data
    
    def _daily_process(
        self,
        trade_date: date,
        trade_dates: List[date],
        day_index: int,
        stock_data: Dict[str, pd.DataFrame],
        stock_pool: List[str]
    ):
        """每日处理
        
        Args:
            trade_date: 当前交易日
            trade_dates: 交易日列表
            day_index: 当前索引
            stock_data: 股票数据
            stock_pool: 股票池
        """
        # 1. 更新持仓价格
        self._update_positions_price(trade_date, stock_data)
        
        # 2. 检查卖出条件
        sell_orders = self._check_sell_conditions(trade_date, trade_dates, day_index)
        
        # 3. 执行卖出
        if sell_orders:
            self._execute_sell(sell_orders, trade_date, stock_data)
        
        # 4. 选股
        if self.portfolio.position_count < self.max_positions:
            buy_candidates = self._select_stocks(trade_date, stock_pool)
            
            # 5. 执行买入
            if buy_candidates:
                self._execute_buy(buy_candidates, trade_date, stock_data)
    
    def _update_positions_price(
        self,
        trade_date: date,
        stock_data: Dict[str, pd.DataFrame]
    ):
        """更新持仓价格"""
        prices = {}
        
        for ts_code in self.portfolio.positions:
            symbol = ts_code.split('.')[0]
            if symbol in stock_data:
                df = stock_data[symbol]
                mask = df['trade_date'].dt.date == trade_date
                if mask.any():
                    prices[ts_code] = df.loc[mask, 'close'].iloc[0]
        
        self.portfolio.update_prices(prices)
    
    def _check_sell_conditions(
        self,
        trade_date: date,
        trade_dates: List[date],
        day_index: int
    ) -> List[Order]:
        """检查卖出条件"""
        sell_orders = []
        
        for ts_code, pos in list(self.portfolio.positions.items()):
            should_sell = False
            
            # 1. 止损
            if pos.profit_pct <= self.stop_loss * 100:
                should_sell = True
                logger.debug(f"止损卖出: {ts_code}")
            
            # 2. 止盈
            if pos.profit_pct >= self.take_profit * 100:
                should_sell = True
                logger.debug(f"止盈卖出: {ts_code}")
            
            # 3. 最大持仓天数
            if day_index > 0:
                hold_days = (trade_date - pos.buy_date).days
                if hold_days >= self.sell_days:
                    should_sell = True
                    logger.debug(f"超时卖出: {ts_code}")
            
            if should_sell:
                order = Order(
                    ts_code=ts_code,
                    direction='sell',
                    shares=pos.shares,
                    order_date=trade_date
                )
                sell_orders.append(order)
        
        return sell_orders
    
    def _execute_sell(
        self,
        orders: List[Order],
        trade_date: date,
        stock_data: Dict[str, pd.DataFrame]
    ):
        """执行卖出"""
        for order in orders:
            symbol = order.ts_code.split('.')[0]
            if symbol in stock_data:
                df = stock_data[symbol]
                mask = df['trade_date'].dt.date == trade_date
                if mask.any():
                    price = df.loc[mask, 'close'].iloc[0]
                    self.portfolio.sell(
                        ts_code=order.ts_code,
                        shares=order.shares,
                        price=price,
                        trade_date=trade_date
                    )
    
    def _select_stocks(
        self,
        trade_date: date,
        stock_pool: List[str]
    ) -> List[str]:
        """选股"""
        try:
            candidates = self.selector.get_buy_candidates(
                trade_date=trade_date,
                stock_pool=stock_pool,
                top_n=self.max_positions - self.portfolio.position_count
            )
            return candidates
        except Exception as e:
            logger.warning(f"选股失败: {e}")
            return []
    
    def _execute_buy(
        self,
        candidates: List[str],
        trade_date: date,
        stock_data: Dict[str, pd.DataFrame]
    ):
        """执行买入"""
        for ts_code in candidates:
            if self.portfolio.position_count >= self.max_positions:
                break
            
            # 计算买入金额
            buy_amount = self.portfolio.cash * self.position_size
            
            symbol = ts_code.split('.')[0]
            if symbol in stock_data:
                df = stock_data[symbol]
                mask = df['trade_date'].dt.date == trade_date
                if mask.any():
                    price = df.loc[mask, 'close'].iloc[0]
                    shares = int(buy_amount / price / 100) * 100  # 整手
                    
                    if shares > 0:
                        self.portfolio.buy(
                            ts_code=ts_code,
                            shares=shares,
                            price=price,
                            trade_date=trade_date
                        )
    
    def _generate_result(self) -> Dict:
        """生成回测结果"""
        history = self.portfolio.get_history_df()
        trades = self.portfolio.get_trade_records_df()
        
        # 计算绩效指标
        if not history.empty and 'profit_pct' in history.columns:
            returns = history['profit_pct'].diff() / 100
            
            result = {
                'initial_capital': self.initial_capital,
                'final_capital': self.portfolio.total_value,
                'total_return': self.portfolio.total_profit_pct,
                'total_trades': len(trades),
                'win_trades': len(trades[trades['profit'] > 0]) if not trades.empty else 0,
                'history': history,
                'trades': trades,
                'positions': self.portfolio.get_positions_df()
            }
            
            # 基准对比
            if not history.empty:
                comparison = self.benchmark.compare(returns)
                result['benchmark_comparison'] = comparison
        else:
            result = {
                'initial_capital': self.initial_capital,
                'final_capital': self.portfolio.total_value,
                'total_return': 0,
                'total_trades': 0,
                'history': history,
                'trades': trades
            }
        
        return result