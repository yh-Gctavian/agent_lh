# -*- coding: utf-8 -*-
"""回测引擎核心"""

from typing import Dict, List, Optional, Any
from datetime import date, datetime, timedelta
import pandas as pd
import numpy as np

from .portfolio import Portfolio
from .matcher import OrderMatcher, Order
from .benchmark import Benchmark
from ..selector.engine import SelectorEngine
from ..data.loader import DataLoader
from ..utils.logger import get_logger

logger = get_logger('backtest_engine')


class BacktestEngine:
    """回测引擎
    
    回测规则：
    - 单票最大10%
    - 最大10只股票
    - 总仓位80%
    - 买入费0.03%，卖出0.13%，滑点0.1%
    """
    
    def __init__(
        self,
        selector: SelectorEngine = None,
        initial_capital: float = 1_000_000.0,
        benchmark_code: str = "000300.SH",
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
        
        self.portfolio = Portfolio(
            initial_capital,
            max_positions,
            single_position_pct,
            max_total_position
        )
        self.matcher = OrderMatcher()
        self.data_loader = DataLoader()
        
        # 回测结果
        self.trade_records: List[Dict] = []
        self.daily_values: List[Dict] = []
        
        logger.info(f"回测引擎初始化: 资金{initial_capital}, 最大持仓{max_positions}")
    
    def run(
        self,
        start_date: str,
        end_date: str,
        stock_pool: List[str] = None,
        rebalance_freq: int = 5  # 调仓频率（天）
    ) -> Dict[str, Any]:
        """运行回测"""
        logger.info(f"开始回测: {start_date} -> {end_date}")
        
        # 获取交易日
        trade_dates = self._get_trade_dates(start_date, end_date)
        logger.info(f"交易日数: {len(trade_dates)}")
        
        # 重置
        self.portfolio.reset()
        self.trade_records = []
        self.daily_values = []
        
        # 加载基准
        self.benchmark.load_data(start_date, end_date)
        
        # 主循环
        last_rebalance = -rebalance_freq
        
        for i, trade_date in enumerate(trade_dates):
            # 更新价格
            self._update_prices(trade_date)
            
            # 记录净值
            self._record_daily(trade_date)
            
            # 调仓
            if i - last_rebalance >= rebalance_freq:
                self._rebalance(trade_date, stock_pool)
                last_rebalance = i
        
        # 计算结果
        result = self._calc_result()
        
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
            current += timedelta(days=1)
        
        return dates
    
    def _update_prices(self, trade_date: date):
        """更新持仓价格"""
        prices = {}
        for ts_code in list(self.portfolio.positions.keys()):
            symbol = ts_code.split('.')[0]
            try:
                df = self.data_loader.load_daily_data(
                    symbol=symbol,
                    start_date=str(trade_date).replace('-', ''),
                    end_date=str(trade_date).replace('-', ''),
                    adjust='qfq'
                )
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
    
    def _rebalance(self, trade_date: date, stock_pool: List[str] = None):
        """调仓"""
        try:
            selected = self.selector.run(
                trade_date=trade_date,
                stock_pool=stock_pool,
                top_n=self.max_positions,
                min_score=70.0
            )
            
            if selected.empty:
                return
            
            target = set(selected['ts_code'].tolist() if 'ts_code' in selected.columns else [])
            current = set(self.portfolio.positions.keys())
            
            # 卖出
            for ts_code in current - target:
                self._sell_stock(ts_code, trade_date)
            
            # 买入
            for ts_code in target - current:
                self._buy_stock(ts_code, trade_date)
                
        except Exception as e:
            logger.warning(f"{trade_date} 调仓失败: {e}")
    
    def _sell_stock(self, ts_code: str, trade_date: date):
        """卖出股票"""
        pos = self.portfolio.get_position(ts_code)
        if not pos:
            return
        
        # 获取次日价格
        next_date = trade_date + timedelta(days=1)
        while next_date.weekday() >= 5:
            next_date += timedelta(days=1)
        
        symbol = ts_code.split('.')[0]
        try:
            df = self.data_loader.load_daily_data(
                symbol=symbol,
                start_date=str(next_date).replace('-', ''),
                end_date=str(next_date).replace('-', ''),
                adjust='qfq'
            )
            if df.empty:
                return
            
            price = self.matcher.get_executed_price(df['open'].iloc[-1], 'sell')
            self.portfolio.sell_all(ts_code, price)
            
            self.trade_records.append({
                'date': next_date,
                'symbol': ts_code,
                'direction': 'sell',
                'shares': pos.shares,
                'price': price
            })
        except:
            pass
    
    def _buy_stock(self, ts_code: str, trade_date: date):
        """买入股票"""
        # 计算买入金额
        buy_amount = self.portfolio.total_value * self.single_position_pct
        if buy_amount > self.portfolio.cash:
            buy_amount = self.portfolio.cash * 0.95  # 预留现金
        
        # 获取次日价格
        next_date = trade_date + timedelta(days=1)
        while next_date.weekday() >= 5:
            next_date += timedelta(days=1)
        
        symbol = ts_code.split('.')[0]
        try:
            df = self.data_loader.load_daily_data(
                symbol=symbol,
                start_date=str(next_date).replace('-', ''),
                end_date=str(next_date).replace('-', ''),
                adjust='qfq'
            )
            if df.empty:
                return
            
            price = self.matcher.get_executed_price(df['open'].iloc[-1], 'buy')
            shares = int(buy_amount / price / 100) * 100  # 整手
            
            if shares > 0:
                self.portfolio.buy(ts_code, shares, price)
                self.trade_records.append({
                    'date': next_date,
                    'symbol': ts_code,
                    'direction': 'buy',
                    'shares': shares,
                    'price': price
                })
        except:
            pass
    
    def _calc_result(self) -> Dict[str, Any]:
        """计算回测结果"""
        if not self.daily_values:
            return {'error': '无数据'}
        
        df = pd.DataFrame(self.daily_values)
        df['return'] = df['total_value'].pct_change()
        df['cum_return'] = (1 + df['return'].fillna(0)).cumprod() - 1
        
        # 最大回撤
        df['peak'] = df['total_value'].expanding().max()
        df['drawdown'] = (df['total_value'] - df['peak']) / df['peak']
        max_dd = df['drawdown'].min()
        
        # 年化收益
        days = len(df)
        total_ret = df['cum_return'].iloc[-1]
        annual_ret = (1 + total_ret) ** (252 / days) - 1 if days > 0 else 0
        
        # 夏普
        sharpe = df['return'].mean() / df['return'].std() * np.sqrt(252) if df['return'].std() > 0 else 0
        
        # 胜率
        trades = pd.DataFrame(self.trade_records)
        if not trades.empty:
            buys = trades[trades['direction'] == 'buy']
            sells = trades[trades['direction'] == 'sell']
            # 简化：计算盈利交易占比
            win_rate = 0.5  # TODO: 精确计算
        else:
            win_rate = 0
        
        return {
            'initial_capital': self.initial_capital,
            'final_value': df['total_value'].iloc[-1],
            'total_return': total_ret,
            'annual_return': annual_ret,
            'max_drawdown': max_dd,
            'sharpe_ratio': sharpe,
            'win_rate': win_rate,
            'trade_count': len(self.trade_records),
            'daily_values': df,
            'trade_records': trades
        }