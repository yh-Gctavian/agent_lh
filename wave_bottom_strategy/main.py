# -*- coding: utf-8 -*-
"""波段抄底策略 - 主入口"""

import argparse
from pathlib import Path
from datetime import date

from config import settings
from data.loader import DataLoader
from data.processor import DataProcessor
from data.cache import DataCache
from selector.engine import SelectorEngine
from backtest.engine import BacktestEngine
from analysis.metrics import PerformanceMetrics
from analysis.reporter import ReportGenerator
from utils.logger import get_logger

logger = get_logger('main')


def run_backtest(start_date: str, end_date: str, initial_capital: float = 1000000):
    """运行完整回测流程
    
    Args:
        start_date: 开始日期
        end_date: 结束日期
        initial_capital: 初始资金
    """
    logger.info("=" * 60)
    logger.info("波段抄底策略 - 回测启动")
    logger.info("=" * 60)
    
    # 1. 初始化组件
    logger.info("[1/5] 初始化组件...")
    data_loader = DataLoader()
    selector = SelectorEngine()
    
    # 2. 加载股票池
    logger.info("[2/5] 加载股票池...")
    stock_pool = data_loader.load_stock_pool('hs300')
    logger.info(f"沪深300成分股: {len(stock_pool)}只")
    
    # 3. 初始化回测引擎
    logger.info("[3/5] 初始化回测引擎...")
    engine = BacktestEngine(
        selector=selector,
        initial_capital=initial_capital,
        max_positions=10,
        single_position_pct=0.10,
        max_total_position=0.80
    )
    
    # 4. 运行回测
    logger.info("[4/5] 执行回测...")
    result = engine.run(
        start_date=start_date,
        end_date=end_date,
        stock_pool=stock_pool,
        rebalance_freq=5
    )
    
    # 5. 生成报告
    logger.info("[5/5] 生成报告...")
    
    if 'error' in result:
        logger.error(f"回测失败: {result['error']}")
        return
    
    # 打印关键指标
    print("\n" + "=" * 60)
    print("回测结果摘要")
    print("=" * 60)
    print(f"初始资金: {result['initial_capital']:,.2f}")
    print(f"最终资产: {result['final_value']:,.2f}")
    print(f"总收益率: {result['total_return']*100:.2f}%")
    print(f"年化收益: {result['annual_return']*100:.2f}%")
    print(f"最大回撤: {result['max_drawdown']*100:.2f}%")
    print(f"夏普比率: {result['sharpe_ratio']:.2f}")
    print(f"交易次数: {result['trade_count']}")
    print("=" * 60)
    
    # 保存报告
    output_dir = Path('output')
    output_dir.mkdir(exist_ok=True)
    
    reporter = ReportGenerator(output_dir)
    report_path = reporter.generate(
        metrics={
            'total_return': result['total_return'],
            'annual_return': result['annual_return'],
            'max_drawdown': result['max_drawdown'],
            'sharpe_ratio': result['sharpe_ratio']
        },
        backtest_result=result['daily_values']
    )
    
    logger.info(f"报告已生成: {report_path}")
    logger.info("回测完成！")


def run_select(trade_date: str = None):
    """执行选股（不回测）
    
    Args:
        trade_date: 交易日期
    """
    if trade_date is None:
        trade_date = date.today()
    
    logger.info(f"执行选股: {trade_date}")
    
    selector = SelectorEngine()
    result = selector.run(
        trade_date=trade_date,
        stock_pool=None,  # 使用沪深300
        top_n=10,
        min_score=70.0
    )
    
    print("\n" + "=" * 60)
    print(f"选股结果 - {trade_date}")
    print("=" * 60)
    print(result.to_string())
    print("=" * 60)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='波段抄底策略')
    parser.add_argument(
        '--mode',
        choices=['backtest', 'select'],
        default='backtest',
        help='运行模式: backtest(回测) / select(选股)'
    )
    parser.add_argument(
        '--start',
        default='2020-01-01',
        help='开始日期 (YYYY-MM-DD)'
    )
    parser.add_argument(
        '--end',
        default='2025-12-31',
        help='结束日期 (YYYY-MM-DD)'
    )
    parser.add_argument(
        '--capital',
        type=float,
        default=1000000,
        help='初始资金'
    )
    
    args = parser.parse_args()
    
    if args.mode == 'backtest':
        run_backtest(args.start, args.end, args.capital)
    else:
        run_select(args.end)


if __name__ == '__main__':
    main()