# -*- coding: utf-8 -*-
"""波段抄底策略 - 主入口"""

import argparse
from pathlib import Path
from datetime import date
import pandas as pd

from config import settings, FACTOR_PARAMS
from data.loader import DataLoader
from data.processor import DataProcessor
from data.cache import DataCache
from factors import (
    KDJFactor, MAFactor, VolumeFactor, 
    RSIFactor, MACDFactor, BollingerFactor
)
from selector.engine import SelectorEngine
from selector.scorer import FactorScorer
from selector.filter import StockFilter
from selector.signal import SignalGenerator
from backtest.engine import BacktestEngine
from analysis.metrics import PerformanceMetrics
from analysis.layering import LayeringAnalysis
from analysis.sensitivity import SensitivityAnalysis, default_param_ranges
from analysis.reporter import ReportGenerator
from utils.logger import get_logger

logger = get_logger('main', settings.log_level, settings.log_file)


def run_backtest(
    start_date: str = None,
    end_date: str = None,
    initial_capital: float = None,
    max_positions: int = 10,
    min_score: float = 70.0,
    stop_loss: float = -0.05,
    take_profit: float = 0.15,
    max_hold_days: int = 5,
    output_dir: str = 'reports'
):
    """运行完整回测流程
    
    Args:
        start_date: 开始日期
        end_date: 结束日期
        initial_capital: 初始资金
        max_positions: 最大持仓数
        min_score: 最低选股得分
        stop_loss: 止损比例
        take_profit: 止盈比例
        max_hold_days: 最大持仓天数
        output_dir: 报告输出目录
    """
    # 使用默认配置
    start_date = start_date or settings.backtest_start
    end_date = end_date or settings.backtest_end
    initial_capital = initial_capital or settings.initial_capital
    
    logger.info("="*50)
    logger.info("波段抄底策略 - 回测启动")
    logger.info(f"回测区间: {start_date} ~ {end_date}")
    logger.info(f"初始资金: {initial_capital:,.0f}")
    logger.info("="*50)
    
    # 1. 初始化组件
    data_loader = DataLoader()
    data_processor = DataProcessor()
    scorer = FactorScorer()
    stock_filter = StockFilter()
    signal_generator = SignalGenerator(min_score=min_score)
    
    selector = SelectorEngine(
        scorer=scorer,
        stock_filter=stock_filter,
        signal_generator=signal_generator,
        data_loader=data_loader
    )
    
    # 2. 运行回测
    backtest_engine = BacktestEngine(
        selector=selector,
        initial_capital=initial_capital,
        max_positions=max_positions,
        min_score=min_score,
        stop_loss=stop_loss,
        take_profit=take_profit,
        sell_days=max_hold_days
    )
    
    result = backtest_engine.run(start_date, end_date)
    
    # 3. 计算绩效指标
    if not result['history'].empty:
        history = result['history']
        returns = history['profit_pct'].diff() / 100 if 'profit_pct' in history.columns else pd.Series()
        
        metrics_calc = PerformanceMetrics(returns)
        metrics = metrics_calc.get_all_metrics(result['trades'])
        
        result['metrics'] = metrics
        
        # 打印关键指标
        logger.info("\n" + "="*50)
        logger.info("回测结果")
        logger.info("="*50)
        logger.info(f"总收益率: {result['total_return']:.2%}")
        logger.info(f"胜率: {metrics.get('win_rate', 0):.2%}")
        logger.info(f"盈亏比: {metrics.get('profit_loss_ratio', 0):.2f}")
        logger.info(f"夏普比率: {metrics.get('sharpe_ratio', 0):.2f}")
        logger.info(f"最大回撤: {metrics.get('max_drawdown', 0):.2%}")
        logger.info(f"交易次数: {result['total_trades']}")
        logger.info("="*50)
    
    # 4. 生成报告
    report_generator = ReportGenerator(Path(output_dir))
    
    report_path = report_generator.generate(
        metrics=result.get('metrics', {}),
        backtest_result=result
    )
    
    logger.info(f"报告已生成: {report_path}")
    
    return result


def run_parameter_optimization(
    start_date: str = None,
    end_date: str = None,
    train_end: str = '2023-12-31'
):
    """参数优化
    
    使用训练集优化参数，测试集验证
    
    Args:
        start_date: 开始日期
        end_date: 结束日期
        train_end: 训练集结束日期
    """
    logger.info("="*50)
    logger.info("参数优化启动")
    logger.info("="*50)
    
    # 参数范围
    param_ranges = {
        'min_score': [60, 70, 80],
        'stop_loss': [-0.05, -0.07, -0.10],
        'take_profit': [0.10, 0.15, 0.20],
        'max_hold_days': [3, 5, 7]
    }
    
    # 训练集回测函数
    def backtest_with_params(params):
        try:
            result = run_backtest(
                start_date=start_date or '2020-01-01',
                end_date=train_end,
                min_score=params.get('min_score', 70),
                stop_loss=params.get('stop_loss', -0.05),
                take_profit=params.get('take_profit', 0.15),
                max_hold_days=params.get('max_hold_days', 5)
            )
            return result.get('metrics', {})
        except:
            return {'sharpe_ratio': -999}
    
    # 运行敏感性分析
    sensitivity = SensitivityAnalysis(param_ranges)
    results = sensitivity.run_analysis(backtest_with_params)
    
    # 找出最优参数
    optimal = sensitivity.find_optimal(results, 'sharpe_ratio')
    
    logger.info(f"\n最优参数: {optimal}")
    
    return optimal, results


def run_full_analysis(output_dir: str = 'reports'):
    """运行完整分析流程
    
    包括：
    1. 回测
    2. 参数优化
    3. 分层分析
    4. 生成最终报告
    
    Args:
        output_dir: 输出目录
    """
    logger.info("="*60)
    logger.info("波段抄底策略 - 完整分析流程")
    logger.info("="*60)
    
    # 1. 基准回测
    logger.info("\n[1/4] 基准回测...")
    base_result = run_backtest(
        start_date='2020-01-01',
        end_date='2025-12-31',
        output_dir=output_dir
    )
    
    # 2. 参数优化
    logger.info("\n[2/4] 参数优化...")
    optimal_params, param_results = run_parameter_optimization()
    
    # 3. 使用最优参数回测
    logger.info("\n[3/4] 最优参数回测...")
    optimal_result = run_backtest(
        start_date='2020-01-01',
        end_date='2025-12-31',
        min_score=optimal_params.get('min_score', 70),
        stop_loss=optimal_params.get('stop_loss', -0.05),
        take_profit=optimal_params.get('take_profit', 0.15),
        max_hold_days=optimal_params.get('max_hold_days', 5),
        output_dir=output_dir
    )
    
    # 4. 生成最终报告
    logger.info("\n[4/4] 生成最终报告...")
    
    report_generator = ReportGenerator(Path(output_dir))
    
    final_report = report_generator.generate(
        metrics=optimal_result.get('metrics', {}),
        backtest_result=optimal_result,
        sensitivity_result=param_results,
        filename='final_report.md'
    )
    
    logger.info(f"\n最终报告: {final_report}")
    
    return {
        'base_result': base_result,
        'optimal_params': optimal_params,
        'optimal_result': optimal_result,
        'report_path': final_report
    }


def select_stocks(trade_date: str = None, top_n: int = 10):
    """选股（实盘模式）
    
    Args:
        trade_date: 交易日期
        top_n: 返回数量
    """
    from datetime import datetime
    
    trade_date = trade_date or datetime.now().strftime('%Y-%m-%d')
    
    logger.info(f"选股日期: {trade_date}")
    
    # 初始化
    selector = SelectorEngine()
    
    # 执行选股
    candidates = selector.get_buy_candidates(
        trade_date=pd.to_datetime(trade_date).date(),
        top_n=top_n
    )
    
    logger.info(f"选中股票: {candidates}")
    
    return candidates


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='波段抄底策略')
    
    parser.add_argument(
        '--mode',
        choices=['backtest', 'optimize', 'full', 'select'],
        default='backtest',
        help='运行模式'
    )
    parser.add_argument('--start', default=settings.backtest_start, help='开始日期')
    parser.add_argument('--end', default=settings.backtest_end, help='结束日期')
    parser.add_argument('--capital', type=float, default=settings.initial_capital, help='初始资金')
    parser.add_argument('--positions', type=int, default=10, help='最大持仓数')
    parser.add_argument('--min-score', type=float, default=70, help='最低选股得分')
    parser.add_argument('--output', default='reports', help='输出目录')
    
    args = parser.parse_args()
    
    if args.mode == 'backtest':
        run_backtest(
            start_date=args.start,
            end_date=args.end,
            initial_capital=args.capital,
            max_positions=args.positions,
            min_score=args.min_score,
            output_dir=args.output
        )
    
    elif args.mode == 'optimize':
        run_parameter_optimization(args.start, args.end)
    
    elif args.mode == 'full':
        run_full_analysis(args.output)
    
    elif args.mode == 'select':
        select_stocks()


if __name__ == '__main__':
    main()