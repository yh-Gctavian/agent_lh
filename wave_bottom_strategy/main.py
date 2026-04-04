# -*- coding: utf-8 -*-
"""Wave Bottom Strategy - Main Entry Point"""

import argparse
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run_backtest(start: str, end: str):
    """Run backtest"""
    logger.info("Starting backtest: %s -> %s" % (start, end))
    
    from backtest.engine import BacktestEngine
    from analysis.metrics import PerformanceMetrics
    
    engine = BacktestEngine()
    result = engine.run(start, end)
    
    logger.info("Backtest completed: Final value %.0f" % result.get('final', 0))
    return result


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Wave Bottom Strategy')
    parser.add_argument('--start', default='2020-01-01', help='Start date')
    parser.add_argument('--end', default='2025-12-31', help='End date')
    
    args = parser.parse_args()
    run_backtest(args.start, args.end)


if __name__ == '__main__':
    main()