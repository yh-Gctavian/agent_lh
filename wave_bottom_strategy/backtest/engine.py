# -*- coding: utf-8 -*-
"""回测引擎"""

from typing import Dict, List, Optional
from datetime import datetime
import pandas as pd
import numpy as np

from .portfolio import Portfolio
from .matcher import OrderMatcher, Order
from .benchmark import Benchmark
from selector.engine import SelectorEngine
from data.loader import DataLoader
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
        position_size: float = 0.1  # 单只股票仓位比例
    ):
        self.selector = selector or SelectorEngine()
        self.initial_capital = initial_capital
        self.max_positions = max_positions
        self.position_size = position_size
        
        self.portfolio = Portfolio(initial_capital)
        self.matcher = OrderMatcher()
        self.benchmark = Benchmark(benchmark_code)
        self.data_loader = DataLoader()
        
        # 记录
        self.trade_records: List[Dict] = []
        self.daily_values: List[Dict] = []
    
    def run(
        self,
        stock_pool: List[str],
        start_date: str,
        end_date: str
    ) -> Dict:
        """运行回测
        
        Args:
            stock_pool: 股票池
            start_date: 开始日期 (YYYYMMDD)
            end_date: 结束日期 (YYYYMMDD)
            
        Returns:
            回测结果
        """
        logger.info(f"回测开始: {start_date} -> {end_date}")
        
        # 加载基准数据
        self.benchmark.load_data(start_date, end_date)
        
        # 获取交易日列表
        trade_dates = self.data_loader.load_trade_calendar(start_date, end_date)
        
        if not trade_dates:
            logger.error("无法获取交易日历")
            return {}
        
        # 遍历每个交易日
        for i, trade_date in enumerate(trade_dates):
            # 每日开盘更新持仓价格
            self._update_portfolio_prices(trade_date)
            
            # 记录每日净值
            self._record_daily_value(trade_date)
            
            # 执行选股（每隔一段时间调仓）
            if self._should_rebalance(trade_date, i):
                self._rebalance(stock_pool, trade_date)
        
        # 计算回测结果
        result = self._calculate_result()
        
        logger.info(f"回测完成: 总收益率={result.get('total_return', 0):.2%}")
        return result
    
    def _should_rebalance(self, trade_date: str, index: int) -> bool:
        """判断是否需要调仓
        
        简化逻辑：每周一调仓
        """
        dt = datetime.strptime(trade_date, '%Y-%m-%d')
        return dt.weekday() == 0  # 周一
    
    def _update_portfolio_prices(self, trade_date: str):
        """更新持仓价格"""
        prices = {}
        for ts_code in list(self.portfolio.positions.keys()):
            symbol = ts_code.split('.')[0]
            try:
                data = self.data_loader.load_daily_data(symbol, trade_date, trade_date)
                if not data.empty:
                    prices[ts_code] = data['open'].iloc[-1]
            except:
                pass
        
        self.portfolio.update_prices(prices)
    
    def _rebalance(self, stock_pool: List[str], trade_date: str):
        """调仓"""
        logger.info(f"调仓: {trade_date}")
        
        # 执行选股
        result = self.selector.run(stock_pool, trade_date)
        
        if result.empty:
            return
        
        # 获取当前持仓
        current_positions = set(self.portfolio.positions.keys())
        
        # 新选出的股票
        new_positions = set(result.head(self.max_positions)['symbol'].tolist())
        
        # 卖出不在新持仓中的股票
        to_sell = current_positions - new_positions
        for ts_code in to_sell:
            pos = self.portfolio.positions[ts_code]
            self.portfolio.sell(ts_code, pos.shares, pos.current_price)
            self.trade_records.append({
                'date': trade_date,
                'action': 'sell',
                'ts_code': ts_code,
                'shares': pos.shares,
                'price': pos.current_price
            })
        
        # 买入新股票
        to_buy = new_positions - current_positions
        for ts_code in to_buy:
            # 获取价格
            symbol = ts_code.split('.')[0]
            try:
                data = self.data_loader.load_daily_data(symbol, trade_date, trade_date)
                if data.empty:
                    continue
                price = data['open'].iloc[-1]
                
                # 计算买入股数
                position_value = self.portfolio.total_value * self.position_size
                shares = int(position_value / price / 100) * 100  # 整手
                
                if shares > 0 and self.portfolio.buy(ts_code, shares, price):
                    self.trade_records.append({
                        'date': trade_date,
                        'action': 'buy',
                        'ts_code': ts_code,
                        'shares': shares,
                        'price': price
                    })
            except Exception as e:
                logger.warning(f"买入{ts_code}失败: {e}")
    
    def _record_daily_value(self, trade_date: str):
        """记录每日净值"""
        self.daily_values.append({
            'date': trade_date,
            'total_value': self.portfolio.total_value,
            'cash': self.portfolio.cash,
            'positions': len(self.portfolio.positions)
        })
    
    def _calculate_result(self) -> Dict:
        """计算回测结果"""
        if not self.daily_values:
            return {}
        
        df = pd.DataFrame(self.daily_values)
        df['return'] = df['total_value'].pct_change()
        
        # 计算指标
        total_return = df['total_value'].iloc[-1] / self.initial_capital - 1
        
        # 年化收益
        days = len(df)
        annual_return = (1 + total_return) ** (252 / days) - 1 if days > 0 else 0
        
        # 最大回撤
        cummax = df['total_value'].cummax()
        drawdown = (df['total_value'] - cummax) / cummax
        max_drawdown = drawdown.min()
        
        # 夏普比率
        sharpe = df['return'].mean() / df['return'].std() * np.sqrt(252) if df['return'].std() > 0 else 0
        
        # 胜率
        win_days = (df['return'] > 0).sum()
        total_days = (df['return'] != 0).sum()
        win_rate = win_days / total_days if total_days > 0 else 0
        
        return {
            'total_return': total_return,
            'annual_return': annual_return,
            'max_drawdown': max_drawdown,
            'sharpe_ratio': sharpe,
            'win_rate': win_rate,
            'total_trades': len(self.trade_records),
            'daily_values': df
        }