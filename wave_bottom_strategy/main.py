# -*- coding: utf-8 -*-
"""波段抄底策略 - 主入口"""

import argparse
from pathlib import Path
from datetime import datetime
import pandas as pd
import sys

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

# 支持两种导入方式
try:
    from wave_bottom_strategy.config import settings, FACTOR_PARAMS, SELECTOR_PARAMS
    from wave_bottom_strategy.data.loader import DataLoader
    from wave_bottom_strategy.data.processor import DataProcessor
    from wave_bottom_strategy.data.cache import DataCache
    from wave_bottom_strategy.selector.engine import SelectorEngine
    from wave_bottom_strategy.backtest.engine import BacktestEngine
    from wave_bottom_strategy.analysis.metrics import PerformanceMetrics
    from wave_bottom_strategy.analysis.layering import LayeringAnalysis
    from wave_bottom_strategy.analysis.sensitivity import SensitivityAnalysis
    from wave_bottom_strategy.analysis.reporter import ReportGenerator
    from wave_bottom_strategy.utils.logger import get_logger
except ImportError:
    from config import settings, FACTOR_PARAMS, SELECTOR_PARAMS
    from data.loader import DataLoader
    from data.processor import DataProcessor
    from data.cache import DataCache
    from selector.engine import SelectorEngine
    from backtest.engine import BacktestEngine
    from analysis.metrics import PerformanceMetrics
    from analysis.layering import LayeringAnalysis
    from analysis.sensitivity import SensitivityAnalysis
    from analysis.reporter import ReportGenerator
    from utils.logger import get_logger

logger = get_logger('main', settings.log_level)


def run_backtest(start_date: str, end_date: str, initial_capital: float = 1000000):
    """运行完整回测流程
    
    Args:
        start_date: 开始日期
        end_date: 结束日期
        initial_capital: 初始资金
    """
    logger.info(f"开始回测: {start_date} ~ {end_date}")
    
    # 初始化组件
    data_loader = DataLoader()
    selector = SelectorEngine(data_loader=data_loader)
    
    # 运行回测
    engine = BacktestEngine(
        selector=selector,
        initial_capital=initial_capital
    )
    
    result = engine.run(start_date, end_date)
    
    # 计算指标
    if 'history' in result and not result['history'].empty:
        history = result['history']
        returns = history['profit_pct'].diff() / 100
        metrics_calc = PerformanceMetrics(returns)
        metrics = metrics_calc.get_all_metrics(result.get('trades'))
        result['metrics'] = metrics
        
        # 打印结果
        logger.info("="*50)
        logger.info("回测结果")
        logger.info("="*50)
        logger.info(f"总收益率: {result['total_return']:.2%}")
        logger.info(f"夏普比率: {metrics.get('sharpe_ratio', 0):.2f}")
        logger.info(f"最大回撤: {metrics.get('max_drawdown', 0):.2%}")
        logger.info(f"胜率: {metrics.get('win_rate', 0):.2%}")
        logger.info("="*50)
    
    return result


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='波段抄底策略')
    parser.add_argument('--mode', choices=['backtest', 'select'], default='backtest')
    parser.add_argument('--start', default='2020-01-01')
    parser.add_argument('--end', default='2025-12-31')
    parser.add_argument('--capital', type=float, default=1000000)
    
    args = parser.parse_args()
    
    if args.mode == 'backtest':
        run_backtest(args.start, args.end, args.capital)


if __name__ == '__main__':
    main()