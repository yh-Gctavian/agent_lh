# -*- coding: utf-8 -*-
"""波段抄底策略主入口"""

import argparse
from pathlib import Path
from datetime import datetime

from wave_bottom_strategy.config import settings, FACTOR_PARAMS, SELECTOR_PARAMS
from wave_bottom_strategy.data.loader import DataLoader
from wave_bottom_strategy.data.processor import DataProcessor
from wave_bottom_strategy.selector.engine import SelectorEngine
from wave_bottom_strategy.backtest.engine import BacktestEngine
from wave_bottom_strategy.analysis.metrics import PerformanceMetrics
from wave_bottom_strategy.analysis.reporter import ReportGenerator
from wave_bottom_strategy.utils.logger import get_logger

logger = get_logger('wave_bottom', settings.log_level, settings.log_file)


def run_backtest(start_date: str, end_date: str, initial_capital: float = 1000000):
    """运行回测
    
    Args:
        start_date: 开始日期 (YYYY-MM-DD)
        end_date: 结束日期 (YYYY-MM-DD)
        initial_capital: 初始资金
    """
    logger.info(f"开始回测: {start_date} -> {end_date}")
    
    # 1. 初始化组件
    engine = BacktestEngine(initial_capital=initial_capital)
    
    # 2. 运行回测
    result = engine.run(start_date, end_date)
    
    if not result or 'daily_df' not in result:
        logger.error("回测失败")
        return
    
    # 3. 计算绩效指标
    daily_df = result['daily_df']
    returns = daily_df['return'].fillna(0)
    
    metrics = PerformanceMetrics(returns)
    all_metrics = metrics.get_all_metrics()
    
    # 添加额外指标
    all_metrics['initial_capital'] = initial_capital
    all_metrics['final_value'] = round(daily_df['value'].iloc[-1], 2)
    all_metrics['total_return'] = round(result['total_return'] * 100, 2)
    all_metrics['trade_count'] = result['trades']
    
    # 4. 生成报告
    reporter = ReportGenerator()
    report_path = reporter.generate(all_metrics, daily_df)
    
    logger.info(f"回测完成，报告: {report_path}")
    
    # 打印关键指标
    print("\n" + "="*50)
    print("波段抄底策略回测结果")
    print("="*50)
    print(f"回测区间: {start_date} ~ {end_date}")
    print(f"初始资金: {initial_capital:,.0f}")
    print(f"最终资金: {all_metrics['final_value']:,.2f}")
    print(f"总收益率: {all_metrics['total_return']:.2f}%")
    print(f"年化收益: {all_metrics['annual_return']:.2f}%")
    print(f"最大回撤: {all_metrics['max_drawdown']:.2f}%")
    print(f"夏普比率: {all_metrics['sharpe_ratio']:.2f}")
    print(f"胜率: {all_metrics['win_rate']:.2f}%")
    print(f"盈亏比: {all_metrics['profit_loss_ratio']:.2f}")
    print(f"交易次数: {all_metrics['trade_count']}")
    print("="*50)
    
    return all_metrics


def run_select(trade_date: str, top_n: int = 10):
    """运行选股
    
    Args:
        trade_date: 交易日期 (YYYY-MM-DD)
        top_n: 返回数量
    """
    logger.info(f"执行选股: {trade_date}")
    
    selector = SelectorEngine()
    
    # 执行选股
    result = selector.run(
        trade_date=datetime.strptime(trade_date, '%Y-%m-%d').date(),
        top_n=top_n,
        min_score=70.0
    )
    
    if result.empty:
        logger.warning("无选股结果")
        return
    
    logger.info(f"选股完成: {len(result)}只")
    
    # 打印结果
    print("\n" + "="*50)
    print(f"波段抄底选股结果 ({trade_date})")
    print("="*50)
    
    cols = ['ts_code', 'total_score']
    available_cols = [c for c in cols if c in result.columns]
    
    print(result[available_cols].to_string(index=False))
    print("="*50)
    
    return result


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='波段抄底策略')
    parser.add_argument('--mode', choices=['backtest', 'select'], default='backtest',
                        help='运行模式: backtest(回测) / select(选股)')
    parser.add_argument('--start', default=settings.backtest_start,
                        help='开始日期 (YYYY-MM-DD)')
    parser.add_argument('--end', default=settings.backtest_end,
                        help='结束日期 (YYYY-MM-DD)')
    parser.add_argument('--capital', type=float, default=1000000,
                        help='初始资金')
    parser.add_argument('--top-n', type=int, default=10,
                        help='选股数量')
    
    args = parser.parse_args()
    
    if args.mode == 'backtest':
        run_backtest(args.start, args.end, args.capital)
    else:
        run_select(args.start, args.top_n)


if __name__ == '__main__':
    main()