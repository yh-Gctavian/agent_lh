# -*- coding: utf-8 -*-
"""波段抄底策略主入口"""

import argparse
from pathlib import Path
import sys

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from config import settings, FACTOR_PARAMS, SELECTOR_PARAMS
from utils.logger import get_logger

logger = get_logger('wave_bottom', settings.log_level, settings.log_file)


def run_backtest(start_date: str, end_date: str, capital: float = None):
    """运行回测
    
    Args:
        start_date: 开始日期
        end_date: 结束日期
        capital: 初始资金
    """
    from run import StrategyRunner
    
    logger.info(f"开始回测: {start_date} -> {end_date}")
    
    runner = StrategyRunner(
        initial_capital=capital or settings.initial_capital,
        train_start=start_date,
        train_end=end_date
    )
    
    results = runner.run_full_pipeline()
    
    logger.info("回测完成")
    return results


def run_optimization():
    """运行参数优化"""
    from optimize.param_optimizer import run_optimization
    
    logger.info("开始参数优化")
    return run_optimization()


def run_integration_test():
    """运行集成测试"""
    from tests.integration_test import run_all_tests
    
    logger.info("运行集成测试")
    return run_all_tests()


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='波段抄底策略')
    parser.add_argument('--mode', 
                        choices=['backtest', 'optimize', 'test'], 
                        default='backtest',
                        help='运行模式: backtest(回测) / optimize(优化) / test(测试)')
    parser.add_argument('--start', 
                        default=settings.backtest_start,
                        help='开始日期 (YYYY-MM-DD)')
    parser.add_argument('--end', 
                        default=settings.backtest_end,
                        help='结束日期 (YYYY-MM-DD)')
    parser.add_argument('--capital', 
                        type=float,
                        default=None,
                        help='初始资金')
    
    args = parser.parse_args()
    
    if args.mode == 'backtest':
        run_backtest(args.start, args.end, args.capital)
    elif args.mode == 'optimize':
        run_optimization()
    elif args.mode == 'test':
        run_integration_test()


if __name__ == '__main__':
    main()