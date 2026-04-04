# -*- coding: utf-8 -*-
"""波段抄底策略主入口"""

import argparse
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run_backtest(start: str, end: str):
    """运行回测"""
    logger.info(f"开始回测: {start} -> {end}")
    
    from backtest.engine import BacktestEngine
    from analysis.metrics import PerformanceMetrics
    
    engine = BacktestEngine()
    result = engine.run(start, end)
    
    logger.info(f"回测完成: 最终净值 {result.get('final', 0):,.0f}")
    return result


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='波段抄底策略')
    parser.add_argument('--start', default='2020-01-01', help='开始日期')
    parser.add_argument('--end', default='2025-12-31', help='结束日期')
    
    args = parser.parse_args()
    run_backtest(args.start, args.end)


if __name__ == '__main__':
    main()