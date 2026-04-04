# -*- coding: utf-8 -*-
"""回测引擎核心 - 整合所有组件"""

from typing import Dict, List, Optional, Tuple
from datetime import date, datetime, timedelta
from pathlib import Path
import pandas as pd
import numpy as np
import json

from wave_bottom_strategy.config.settings import settings, BacktestConfig
from wave_bottom_strategy.data.loader import DataLoader
from wave_bottom_strategy.selector.engine import SelectorEngine
from .portfolio import Portfolio, FeeCalculator, PositionSizer, Position, TradeRecord
from .matcher import OrderMatcher, Order, OrderStatus
from .benchmark import Benchmark
from .metrics import PerformanceMetrics, TradeAnalyzer
from .visualizer import BacktestVisualizer

from wave_bottom_strategy.utils.logger import get_logger

logger = get_logger('backtest_engine')


class BacktestResult:
    """回测结果容器"""
    
    def __init__(self):
        self.daily_values: pd.DataFrame = pd.DataFrame()
        self.trade_records: pd.DataFrame = pd.DataFrame()
        self.benchmark_values: pd.DataFrame = pd.DataFrame()
        self.metrics: Dict = {}
        self.trade_analysis: Dict = {}
        self.chart_paths: Dict = {}
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            'metrics': self.metrics,
            'trade_analysis': self.trade_analysis,
            'chart_paths': self.chart_paths,
            'summary': {
                'total_trades': len(self.trade_records),
                'total_days': len(self.daily_values),
                'final_value': self.daily_values['total_value'].iloc[-1] if not self.daily_values.empty else 0
            }
        }
    
    def save(self, path: Path):
        """保存结果"""
        path = Path(path)
        path.mkdir(parents=True, exist_ok=True)
        
        # 保存数据
        if not self.daily_values.empty:
            self.daily_values.to_csv(path / 'daily_values.csv', index=False)
        
        if not self.trade_records.empty:
            self.trade_records.to_csv(path / 'trade_records.csv', index=False)
        
        if not self.benchmark_values.empty:
            self.benchmark_values.to_csv(path / 'benchmark_values.csv', index=False)
        
        # 保存指标
        with open(path / 'metrics.json', 'w', encoding='utf-8') as f:
            json.dump(self.metrics, f, ensure_ascii=False, indent=2)
        
        logger.info(f"回测结果已保存: {path}")


class BacktestEngine:
    """回测引擎
    
    整合所有组件，执行完整回测流程：
    1. 数据加载
    2. 选股信号生成
    3. 订单创建（T日信号）
    4. 订单撮合（T+1开盘价成交）
    5. 持仓更新
    6. 每日资产记录
    7. 绩效计算
    8. 可视化生成
    """
    
    def __init__(
        self,
        config: BacktestConfig = None,
        initial_capital: float = None,
        data_loader: DataLoader = None
    ):
        """初始化
        
        Args:
            config: 回测配置
            initial_capital: 初始资金
            data_loader: 数据加载器
        """
        self.config = config or settings.backtest
        self.initial_capital = initial_capital or settings.initial_capital
        
        # 数据加载器
        self.data_loader = data_loader or DataLoader()
        
        # 选股引擎
        self.selector = SelectorEngine()
        
        # 费用计算器
        self.fee_calc = FeeCalculator(
            commission_rate=self.config.commission_rate,
            min_commission=self.config.min_commission,
            stamp_duty_rate=self.config.stamp_duty_rate,
            transfer_fee_rate=self.config.transfer_fee_rate,
            slippage_rate=self.config.slippage_rate
        )
        
        # 仓位管理
        self.position_sizer = PositionSizer(
            mode=self.config.position_mode,
            max_positions=self.config.max_positions,
            position_size=self.config.position_size
        )
        
        # 组合管理
        self.portfolio = Portfolio(
            initial_capital=self.initial_capital,
            fee_calculator=self.fee_calc,
            position_sizer=self.position_sizer
        )
        
        # 订单撮合
        self.matcher = OrderMatcher(
            data_loader=self.data_loader,
            slippage=self.config.slippage_rate,
            commission_rate=self.config.commission_rate,
            min_commission=self.config.min_commission,
            stamp_duty_rate=self.config.stamp_duty_rate
        )
        
        # 基准
        self.benchmark = Benchmark()
        
        # 绩效计算
        self.metrics_calc = PerformanceMetrics()
        self.trade_analyzer = TradeAnalyzer()
        
        # 可视化
        self.visualizer = BacktestVisualizer()
        
        # 交易日期列表
        self.trade_dates: List[date] = []
        
        # 股票池
        self.stock_pool: List[str] = []
    
    def run(
        self,
        start_date: str,
        end_date: str,
        stock_pool: List[str] = None,
        save_result: bool = True,
        result_path: Path = None
    ) -> BacktestResult:
        """运行回测
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            stock_pool: 股票池
            save_result: 是否保存结果
            result_path: 结果保存路径
            
        Returns:
            回测结果
        """
        logger.info(f"开始回测: {start_date} -> {end_date}")
        
        # 初始化
        self._init_run(start_date, end_date, stock_pool)
        
        # 加载基准数据
        self.benchmark.load_data(start_date, end_date)
        
        # 主循环
        for i, trade_date in enumerate(self.trade_dates):
            # 每日开盘处理
            self._process_daily_open(trade_date)
            
            # 记录每日资产
            self.portfolio.record_daily(trade_date)
            
            # 调仓检查
            if i % self.config.rebalance_freq == 0:
                self._rebalance(trade_date)
            
            # 检查止损止盈
            if self.config.enable_stop_loss or self.config.enable_take_profit:
                self._check_stop_conditions(trade_date)
            
            # 更新持仓天数
            self.portfolio.update_holding_days()
        
        # 计算结果
        result = self._calc_result()
        
        # 保存
        if save_result:
            path = result_path or settings.result_dir / f'backtest_{datetime.now().strftime("%Y%m%d_%H%M%S")}'
            result.save(path)
        
        logger.info(f"回测完成: 收益率 {result.metrics.get('cumulative_return', 0)*100:.2f}%")
        
        return result
    
    def _init_run(self, start_date: str, end_date: str, stock_pool: List[str]):
        """初始化回测"""
        # 重置组合
        self.portfolio = Portfolio(
            initial_capital=self.initial_capital,
            fee_calculator=self.fee_calc,
            position_sizer=self.position_sizer
        )
        
        # 清空订单
        self.matcher.clear_pending()
        self.matcher.processed_orders = []
        
        # 获取交易日期
        self.trade_dates = self._get_trade_dates(start_date, end_date)
        
        # 加载股票池
        if stock_pool is None:
            stock_pool = self.data_loader.load_stock_pool('hs300')
        self.stock_pool = stock_pool
        
        logger.info(f"初始化完成: {len(self.trade_dates)}交易日, {len(self.stock_pool)}只股票")
    
    def _get_trade_dates(self, start: str, end: str) -> List[date]:
        """获取交易日期列表"""
        # 简化：使用工作日
        dates = pd.date_range(start, end, freq='B')
        return [d.date() for d in dates]
    
    def _process_daily_open(self, trade_date: date):
        """每日开盘处理"""
        # 处理待成交订单（T+1成交）
        filled_orders, cancelled_orders = self.matcher.process_orders(trade_date)
        
        # 执行成交订单
        for order in filled_orders:
            if order.direction == 'buy':
                self.portfolio.buy(
                    order.ts_code,
                    order.fill_shares,
                    order.fill_price,
                    trade_date
                )
            else:
                self.portfolio.sell(
                    order.ts_code,
                    order.fill_shares,
                    order.fill_price,
                    trade_date
                )
        
        # 更新持仓价格
        self._update_prices(trade_date)
    
    def _update_prices(self, trade_date: date):
        """更新持仓价格"""
        prices = {}
        for ts_code in self.portfolio.positions:
            symbol = ts_code.split('.')[0]
            df = self.data_loader.load_daily_data(
                symbol, str(trade_date).replace('-', ''), str(trade_date).replace('-', '')
            )
            if not df.empty:
                prices[ts_code] = df['close'].iloc[-1]
        
        self.portfolio.update_prices(prices)
    
    def _rebalance(self, trade_date: date):
        """调仓"""
        logger.info(f"调仓日期: {trade_date}")
        
        try:
            # 选股
            selected = self.selector.run(
                self.stock_pool,
                str(trade_date).replace('-', ''),
                None
            )
            
            if selected.empty:
                return
            
            # 过滤得分不足的
            selected = selected[selected['signal'] == 1]
            
            if selected.empty:
                # 清仓
                self._clear_positions(trade_date)
                return
            
            # 计算目标仓位
            position_sizes = self.position_sizer.calc_position_sizes(
                self.portfolio.total_value,
                selected,
                self.portfolio.positions
            )
            
            # 获取目标股票列表
            target_stocks = list(position_sizes.keys())
            
            # 卖出不在目标中的
            for ts_code in list(self.portfolio.positions.keys()):
                if ts_code not in target_stocks:
                    self.matcher.create_order(
                        ts_code, 'sell',
                        self.portfolio.positions[ts_code].shares,
                        trade_date
                    )
            
            # 买入目标股票
            for ts_code, amount in position_sizes.items():
                # 获取价格
                symbol = ts_code.split('.')[0]
                df = self.data_loader.load_daily_data(
                    symbol, str(trade_date).replace('-', ''), str(trade_date).replace('-', '')
                )
                
                if df.empty:
                    continue
                
                price = df['close'].iloc[-1]
                shares = self.position_sizer.calc_shares(amount, price)
                
                if shares > 0:
                    self.matcher.create_order(ts_code, 'buy', shares, trade_date)
            
            logger.info(f"调仓订单: {len(self.matcher.pending_orders)}个")
            
        except Exception as e:
            logger.warning(f"调仓失败: {e}")
    
    def _clear_positions(self, trade_date: date):
        """清仓"""
        for ts_code, pos in self.portfolio.positions.items():
            self.matcher.create_order(ts_code, 'sell', pos.shares, trade_date)
    
    def _check_stop_conditions(self, trade_date: date):
        """检查止损止盈"""
        for ts_code, pos in self.portfolio.positions.items():
            # 止损
            if self.config.enable_stop_loss:
                if pos.profit_pct <= -self.config.stop_loss_pct:
                    self.matcher.create_order(ts_code, 'sell', pos.shares, trade_date)
                    logger.info(f"止损卖出: {ts_code}")
            
            # 止盈
            if self.config.enable_take_profit:
                if pos.profit_pct >= self.config.take_profit_pct:
                    self.matcher.create_order(ts_code, 'sell', pos.shares, trade_date)
                    logger.info(f"止盈卖出: {ts_code}")
            
            # 最大持仓天数
            if pos.hold_days >= self.config.max_holding_days:
                self.matcher.create_order(ts_code, 'sell', pos.shares, trade_date)
                logger.info(f"超时卖出: {ts_code}")
    
    def _calc_result(self) -> BacktestResult:
        """计算回测结果"""
        result = BacktestResult()
        
        # 每日资产
        result.daily_values = self.portfolio.get_daily_values()
        
        # 交易记录
        result.trade_records = self.portfolio.get_trade_records()
        
        # 基准数据
        if self.benchmark.data is not None:
            bench_df = self.benchmark.data.copy()
            bench_df['total_value'] = bench_df['close'] / bench_df['close'].iloc[0] * self.initial_capital
            result.benchmark_values = bench_df
        
        # 绩效指标
        result.metrics = self.metrics_calc.generate_report(
            result.daily_values,
            result.trade_records,
            result.benchmark_values
        )
        
        # 交易分析
        if not result.trade_records.empty:
            result.trade_analysis = self.trade_analyzer.analyze_trades(result.trade_records)
        
        # 可视化
        result.chart_paths = self.visualizer.generate_full_report(
            result.daily_values,
            result.trade_records,
            result.benchmark_values,
            result.metrics
        )
        
        return result


def run_backtest(
    start_date: str = "2020-01-01",
    end_date: str = "2025-12-31",
    stock_pool: List[str] = None,
    initial_capital: float = 1_000_000.0
) -> BacktestResult:
    """便捷回测函数
    
    Args:
        start_date: 开始日期
        end_date: 结束日期
        stock_pool: 股票池
        initial_capital: 初始资金
        
    Returns:
        回测结果
    """
    engine = BacktestEngine(initial_capital=initial_capital)
    return engine.run(start_date, end_date, stock_pool)