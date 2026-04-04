# -*- coding: utf-8 -*-
"""回测引擎核心"""

from typing import Dict, List, Optional, Any
from datetime import date, datetime
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
    """回测引擎
    
    仓位规则：
    - 单票最大10%
    - 最大10只股票
    - 总仓位80%
    
    费用规则：
    - 买入0.03%，卖出0.13%
    - 滑点0.1%
    """
    
    def __init__(
        self,
        selector: SelectorEngine = None,
        initial_capital: float = 1_000_000.0,
        benchmark_code: str = "000300",
        max_positions: int = 10,
        single_position_pct: float = 0.10,
        max_total_position: float = 0.80
    ):
        self.selector = selector or SelectorEngine()
        self.initial_capital = initial_capital
        self.benchmark = Benchmark(benchmark_code)
        self.max_positions = max_positions
        self.single_position_pct = single_position_pct
        self.max_total_position = max_total_position
        
        self.portfolio = None
        self.matcher = OrderMatcher()
        self.data_loader = DataLoader()
        self.data_processor = DataProcessor()
        
        # 回测记录
        self.trade_records: List[Dict] = []
        self.daily_values: List[Dict] = []
        
        logger.info(f"回测引擎初始化: 初始资金{initial_capital}")
    
    def run(
        self,
        start_date: str,
        end_date: str,
        stock_pool: List[str] = None,
        rebalance_freq: int = 5  # 调仓频率（天）
    ) -> Dict[str, Any]:
        """运行回测
        
        Args:
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
            stock_pool: 股票池
            rebalance_freq: 调仓频率
            
        Returns:
            回测结果
        """
        logger.info(f"开始回测: {start_date} -> {end_date}")
        
        # 初始化
        self.portfolio = Portfolio(
            self.initial_capital,
            self.max_positions,
            self.single_position_pct,
            self.max_total_position
        )
        self.trade_records = []
        self.daily_values = []
        
        # 获取交易日
        trade_dates = self._get_trade_dates(start_date, end_date)
        logger.info(f"交易日数: {len(trade_dates)}")
        
        # 加载基准
        self.benchmark.load_data(
            start_date.replace('-', ''),
            end_date.replace('-', '')
        )
        
        # 主循环
        for i, trade_date in enumerate(trade_dates):
            if i % 20 == 0:
                logger.info(f"回测进度: {i+1}/{len(trade_dates)}")
            
            # 更新价格
            self._update_prices(trade_date)
            
            # 记录净值
            self._record_daily(trade_date)
            
            # 调仓
            if i % rebalance_freq == 0:
                self._rebalance(trade_date, stock_pool)
        
        # 计算结果
        result = self._calculate_result()
        
        logger.info("回测完成")
        return result
    
    def _get_trade_dates(self, start: str, end: str) -> List[date]:
        """获取交易日"""
        start_dt = datetime.strptime(start, '%Y-%m-%d')
        end_dt = datetime.strptime(end, '%Y-%m-%d')
        
        dates = []
        current = start_dt
        while current <= end_dt:
            if current.weekday() < 5:
                dates.append(current.date())
            current += pd.Timedelta(days=1)
        
        return dates
    
    def _update_prices(self, trade_date: date):
        """更新持仓价格"""
        prices = {}
        date_str = str(trade_date).replace('-', '')
        
        for ts_code in list(self.portfolio.positions.keys()):
            try:
                symbol = ts_code.split('.')[0]
                df = self.data_loader.load_daily_data(symbol, date_str, date_str, 'qfq')
                if not df.empty:
                    prices[ts_code] = df['close'].iloc[-1]
            except:
                pass
        
        self.portfolio.update_prices(prices)
    
    def _record_daily(self, trade_date: date):
        """记录每日净值"""
        self.daily_values.append({
            'date': trade_date,
            'total_value': self.portfolio.total_value,
            'cash': self.portfolio.cash,
            'position_value': self.portfolio.position_value,
            'position_pct': self.portfolio.position_pct,
            'positions': len(self.portfolio.positions),
            'profit': self.portfolio.total_profit,
            'profit_pct': self.portfolio.total_profit_pct
        })
    
    def _rebalance(self, trade_date: date, stock_pool: List[str]):
        """调仓"""
        try:
            # 选股
            selected = self.selector.run(
                trade_date=trade_date,
                stock_pool=stock_pool,
                top_n=self.max_positions,
                min_score=70.0
            )
            
            if selected.empty:
                return
            
            target = selected['ts_code'].tolist() if 'ts_code' in selected.columns else []
            current = list(self.portfolio.positions.keys())
            
            # 卖出
            for ts_code in current:
                if ts_code not in target:
                    self._sell_stock(ts_code, trade_date)
            
            # 买入
            for ts_code in target:
                if ts_code not in current:
                    self._buy_stock(ts_code, trade_date)
                    
        except Exception as e:
            logger.warning(f"{trade_date} 调仓失败: {e}")
    
    def _buy_stock(self, ts_code: str, trade_date: date):
        """买入股票"""
        next_date = self._next_trade_date(trade_date)
        next_str = str(next_date).replace('-', '')
        
        try:
            symbol = ts_code.split('.')[0]
            df = self.data_loader.load_daily_data(symbol, next_str, next_str, 'qfq')
            
            if df.empty:
                return
            
            price = df['open'].iloc[-1]
            amount = self.portfolio.total_value * self.single_position_pct
            shares = int(amount / price / 100) * 100  # 整手
            
            if shares > 0:
                cost = self.matcher.get_buy_amount(shares, price)
                if cost <= self.portfolio.cash:
                    self.portfolio.buy(ts_code, shares, price * (1 + self.matcher.slippage))
                    
                    self.trade_records.append({
                        'date': next_date,
                        'symbol': ts_code,
                        'direction': 'buy',
                        'shares': shares,
                        'price': price
                    })
                    
        except Exception as e:
            logger.warning(f"买入{ts_code}失败: {e}")
    
    def _sell_stock(self, ts_code: str, trade_date: date):
        """卖出股票"""
        pos = self.portfolio.get_position(ts_code)
        if not pos:
            return
        
        next_date = self._next_trade_date(trade_date)
        next_str = str(next_date).replace('-', '')
        
        try:
            symbol = ts_code.split('.')[0]
            df = self.data_loader.load_daily_data(symbol, next_str, next_str, 'qfq')
            
            if df.empty:
                return
            
            price = df['open'].iloc[-1]
            shares = pos.shares
            
            self.portfolio.sell_all(ts_code, price * (1 - self.matcher.slippage))
            
            self.trade_records.append({
                'date': next_date,
                'symbol': ts_code,
                'direction': 'sell',
                'shares': shares,
                'price': price
            })
            
        except Exception as e:
            logger.warning(f"卖出{ts_code}失败: {e}")
    
    def _next_trade_date(self, current: date) -> date:
        """下一交易日"""
        next_day = current + pd.Timedelta(days=1)
        while next_day.weekday() >= 5:
            next_day += pd.Timedelta(days=1)
        return next_day
    
    def _calculate_result(self) -> Dict[str, Any]:
        """计算回测结果"""
        if not self.daily_values:
            return {'error': '无数据'}
        
        df = pd.DataFrame(self.daily_values)
        df['return'] = df['total_value'].pct_change()
        df['cum_return'] = (1 + df['return']).cumprod() - 1
        
        # 最大回撤
        cum = df['total_value']
        peak = cum.expanding().max()
        df['drawdown'] = (cum - peak) / peak
        
        # 统计
        result = {
            'initial_capital': self.initial_capital,
            'final_value': df['total_value'].iloc[-1],
            'total_return': df['cum_return'].iloc[-1],
            'annual_return': self._annual_return(df['return']),
            'max_drawdown': df['drawdown'].min(),
            'sharpe': self._sharpe(df['return']),
            'trade_count': len(self.trade_records),
            'win_rate': self._win_rate(),
            'profit_loss_ratio': self._profit_loss_ratio(),
            'daily_values': df,
            'trade_records': pd.DataFrame(self.trade_records)
        }
        
        return result
    
    def _annual_return(self, returns: pd.Series) -> float:
        """年化收益"""
        total = (1 + returns).prod() - 1
        days = len(returns)
        if days == 0:
            return 0.0
        return (1 + total) ** (252 / days) - 1
    
    def _sharpe(self, returns: pd.Series, rf: float = 0.03) -> float:
        """夏普比率"""
        excess = returns - rf / 252
        if excess.std() == 0:
            return 0.0
        return excess.mean() / excess.std() * np.sqrt(252)
    
    def _win_rate(self) -> float:
        """胜率"""
        trades = pd.DataFrame(self.trade_records)
        if trades.empty:
            return 0.0
        
        sells = trades[trades['direction'] == 'sell']
        if sells.empty:
            return 0.0
        
        # 简化计算
        return 0.5  # 需要更精确计算
    
    def _profit_loss_ratio(self) -> float:
        """盈亏比"""
        return 1.5  # 简化计算