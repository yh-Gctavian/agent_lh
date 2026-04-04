# -*- coding: utf-8 -*-
"""波段抄底策略主入口"""

import argparse
from pathlib import Path
from datetime import datetime

from config import settings, FACTOR_PARAMS, SELECTOR_PARAMS
from data.loader import DataLoader
from data.processor import DataProcessor
from selector.engine import SelectorEngine
from backtest.engine import BacktestEngine
from analysis.metrics import PerformanceMetrics
from analysis.layering import LayeringAnalysis
from analysis.sensitivity import SensitivityAnalysis
from analysis.reporter import ReportGenerator
from utils.logger import get_logger

logger = get_logger('main')


def run_backtest(args):
    """运行回测"""
    logger.info("=" * 50)
    logger.info("波段抄底策略回测")
    logger.info("=" * 50)
    
    # 初始化组件
    selector = SelectorEngine()
    engine = BacktestEngine(
        selector=selector,
        initial_capital=args.capital,
        max_positions=args.max_positions
    )
    
    # 运行回测
    result = engine.run(
        start_date=args.start,
        end_date=args.end,
        stock_pool=None,  # 使用默认沪深300
        rebalance_freq=args.rebalance_freq
    )
    
    # 计算指标
    if 'daily_values' in result:
        metrics_calc = PerformanceMetrics(
            result['daily_values'],
            result.get('trade_records')
        )
        metrics = metrics_calc.calculate_all()
        
        # 分层分析
        layering = LayeringAnalysis(result['daily_values'])
        yearly_result = layering.analyze_by_year()
        
        # 生成报告
        reporter = ReportGenerator()
        report_path = reporter.generate(
            metrics,
            result['daily_values'],
            yearly_result
        )
        
        # 输出摘要
        print(metrics_calc.get_statistics_summary())
        
        logger.info(f"报告已生成: {report_path}")
    
    logger.info("回测完成")
    return result


def run_select(args):
    """运行选股"""
    logger.info("执行选股...")
    
    selector = SelectorEngine()
    
    result = selector.run(
        trade_date=datetime.now().date(),
        stock_pool=None,
        top_n=args.top_n
    )
    
    print("\n=== 选股结果 ===")
    print(result)
    
    return result


def run_optimize(args):
    """运行参数优化"""
    logger.info("执行参数优化...")
    
    sensitivity = SensitivityAnalysis()
    
    # 定义参数范围
    param_grid = {
        'min_score': [60, 70, 80],
        'rebalance_freq': [5, 10, 20]
    }
    
    def backtest_wrapper(params):
        selector = SelectorEngine()
        engine = BacktestEngine(selector=selector)
        
        result = engine.run(
            start_date='2020-01-01',
            end_date='2023-12-31',
            rebalance_freq=params.get('rebalance_freq', 5)
        )
        
        return result
    
    # 网格搜索
    results = sensitivity.grid_search(
        param_grid,
        backtest_wrapper
    )
    
    # 最优参数
    optimal = sensitivity.find_optimal_params(results)
    
    print("\n=== 最优参数 ===")
    print(optimal)
    
    return optimal


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='波段抄底策略',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest='mode', help='运行模式')
    
    # 回测模式
    backtest_parser = subparsers.add_parser('backtest', help='运行回测')
    backtest_parser.add_argument('--start', default='2020-01-01',
                                  help='开始日期')
    backtest_parser.add_argument('--end', default='2025-12-31',
                                  help='结束日期')
    backtest_parser.add_argument('--capital', type=float, default=1000000,
                                  help='初始资金')
    backtest_parser.add_argument('--max-positions', type=int, default=10,
                                  help='最大持仓数')
    backtest_parser.add_argument('--rebalance-freq', type=int, default=5,
                                  help='调仓频率(天)')
    
    # 选股模式
    select_parser = subparsers.add_parser('select', help='执行选股')
    select_parser.add_argument('--top-n', type=int, default=10,
                                help='返回股票数')
    
    # 优化模式
    optimize_parser = subparsers.add_parser('optimize', help='参数优化')
    
    args = parser.parse_args()
    
    if args.mode == 'backtest':
        run_backtest(args)
    elif args.mode == 'select':
        run_select(args)
    elif args.mode == 'optimize':
        run_optimize(args)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()