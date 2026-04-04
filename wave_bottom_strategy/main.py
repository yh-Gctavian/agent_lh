# -*- coding: utf-8 -*-
"""主入口 - 整体流程联调"""

import argparse
from pathlib import Path
from datetime import datetime

from config import settings, FACTOR_PARAMS
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

logger = get_logger('main')


def run_backtest(start_date: str, end_date: str, initial_capital: float = 1000000):
    """运行完整回测流程
    
    Args:
        start_date: 开始日期
        end_date: 结束日期
        initial_capital: 初始资金
    """
    logger.info("=" * 50)
    logger.info("波段抄底策略 - 回测启动")
    logger.info("=" * 50)
    
    # 1. 初始化组件
    logger.info("[1/5] 初始化组件...")
    data_loader = DataLoader()
    data_processor = DataProcessor()
    selector = SelectorEngine()
    
    # 2. 加载股票池
    logger.info("[2/5] 加载股票池...")
    stock_pool = data_loader.load_stock_pool('hs300')
    logger.info(f"沪深300成分股: {len(stock_pool)}只")
    
    # 3. 执行选股
    logger.info("[3/5] 执行选股...")
    # 简化：使用最近交易日
    trade_date = datetime.now().date()
    selected = selector.run(trade_date, stock_pool, top_n=10)
    logger.info(f"选股结果: {len(selected)}只")
    
    # 4. 执行回测
    logger.info("[4/5] 执行回测...")
    backtest_engine = BacktestEngine(
        selector=selector,
        initial_capital=initial_capital
    )
    
    result = backtest_engine.run(
        start_date=start_date,
        end_date=end_date,
        stock_pool=stock_pool[:50]  # 简化：使用前50只
    )
    
    # 5. 生成报告
    logger.info("[5/5] 生成报告...")
    reporter = ReportGenerator()
    
    metrics = PerformanceMetrics(result.get('daily_values'))
    metrics_dict = metrics.get_all_metrics(result.get('trade_records'))
    
    # 分层分析
    layering = LayeringAnalysis(result.get('daily_values'))
    layer_result = layering.get_full_report()
    
    # 生成报告
    report_path = reporter.generate(
        metrics=metrics_dict,
        daily_values=result.get('daily_values'),
        layer_result=layer_result,
        trades=result.get('trade_records')
    )
    
    logger.info(f"报告已生成: {report_path}")
    
    # 打印结果摘要
    print("\n" + "=" * 50)
    print("回测结果摘要")
    print("=" * 50)
    for key, value in metrics_dict.items():
        print(f"{key}: {value}")
    
    return result, metrics_dict


def run_optimization(start_date: str, end_date: str):
    """参数优化
    
    Args:
        start_date: 开始日期
        end_date: 结束日期
    """
    logger.info("=" * 50)
    logger.info("参数优化分析")
    logger.info("=" * 50)
    
    # 定义参数范围
    param_ranges = {
        'min_score': [60, 65, 70, 75, 80],
        'kdj_threshold': [15, 20, 25, 30],
        'max_positions': [5, 8, 10, 15],
    }
    
    # 敏感性分析
    sensitivity = SensitivityAnalysis()
    
    # 简化的回测函数
    def simple_backtest(params):
        # 模拟回测结果
        import random
        return {
            'total_return': random.uniform(-0.2, 0.5),
            'sharpe_ratio': random.uniform(-1, 2),
            'max_drawdown': random.uniform(-0.3, -0.05),
            'win_rate': random.uniform(0.3, 0.7)
        }
    
    # 网格搜索
    results = sensitivity.grid_search(param_ranges, simple_backtest)
    
    # 找最优参数
    optimal = sensitivity.find_optimal(results, metric='sharpe_ratio')
    
    print("\n最优参数组合:")
    print(optimal.to_string())
    
    return optimal


def generate_recommendation(metrics: dict, optimal_params: dict) -> dict:
    """生成策略建议
    
    Args:
        metrics: 绩效指标
        optimal_params: 最优参数
        
    Returns:
        策略建议
    """
    recommendation = {
        '最优参数': optimal_params,
        '建议资金规模': '100-500万',
        '建议持仓周期': '5-15个交易日',
        '风险等级': '中高风险',
        '适合市场环境': '震荡市/熊市反弹',
    }
    
    # 根据夏普比率调整建议
    sharpe = float(metrics.get('sharpe_ratio', 0))
    if sharpe > 1.5:
        recommendation['策略评价'] = '优秀'
        recommendation['建议资金规模'] = '200-1000万'
    elif sharpe > 1.0:
        recommendation['策略评价'] = '良好'
        recommendation['建议资金规模'] = '100-500万'
    elif sharpe > 0.5:
        recommendation['策略评价'] = '一般'
        recommendation['建议资金规模'] = '50-200万'
    else:
        recommendation['策略评价'] = '需优化'
        recommendation['建议资金规模'] = '建议谨慎使用'
    
    return recommendation


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='波段抄底策略')
    parser.add_argument('--mode', choices=['backtest', 'optimize', 'select'], 
                        default='backtest', help='运行模式')
    parser.add_argument('--start', default='2020-01-01', help='开始日期')
    parser.add_argument('--end', default='2025-12-31', help='结束日期')
    parser.add_argument('--capital', type=float, default=1000000, help='初始资金')
    
    args = parser.parse_args()
    
    if args.mode == 'backtest':
        result, metrics = run_backtest(args.start, args.end, args.capital)
        
    elif args.mode == 'optimize':
        optimal = run_optimization(args.start, args.end)
        
    elif args.mode == 'select':
        # 单独选股模式
        selector = SelectorEngine()
        selected = selector.run(datetime.now().date(), top_n=10)
        print("\n选股结果:")
        print(selected.to_string())


if __name__ == '__main__':
    main()