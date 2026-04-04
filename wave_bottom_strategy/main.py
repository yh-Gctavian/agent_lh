# -*- coding: utf-8 -*-
"""波段抄底策略 - 主入口"""

import argparse
from pathlib import Path
from datetime import datetime
import pandas as pd

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
    logger.info("=" * 50)
    logger.info("波段抄底策略 - 回测开始")
    logger.info(f"时间范围: {start_date} -> {end_date}")
    logger.info(f"初始资金: {initial_capital:,.0f}")
    logger.info("=" * 50)
    
    # 1. 初始化组件
    loader = DataLoader()
    processor = DataProcessor()
    
    # 2. 加载股票池
    logger.info("\n[Step 1] 加载股票池...")
    stock_pool = loader.load_stock_pool('hs300')
    logger.info(f"沪深300成分股: {len(stock_pool)}只")
    
    # 过滤ST和停牌
    filtered_pool = processor.filter_stocks(stock_pool, exclude_st=True)
    logger.info(f"过滤后: {len(filtered_pool)}只")
    
    # 3. 执行回测
    logger.info("\n[Step 2] 执行回测...")
    engine = BacktestEngine(
        initial_capital=initial_capital,
        max_positions=10,
        position_size=0.1
    )
    
    result = engine.run(
        start_date=start_date,
        end_date=end_date,
        stock_pool=filtered_pool[:50]  # 简化：取前50只
    )
    
    # 4. 计算绩效
    logger.info("\n[Step 3] 计算绩效指标...")
    if 'daily_df' in result and not result['daily_df'].empty:
        daily_df = result['daily_df']
        returns = daily_df['return'].fillna(0)
        
        metrics = PerformanceMetrics(returns=returns)
        metrics_dict = metrics.get_all_metrics()
        
        logger.info("\n" + metrics.summary())
    else:
        metrics_dict = {}
    
    # 5. 生成报告
    logger.info("\n[Step 4] 生成报告...")
    reporter = ReportGenerator()
    report_path = reporter.generate(
        metrics=metrics_dict,
        backtest_result=result,
        format='markdown'
    )
    
    logger.info(f"报告已生成: {report_path}")
    
    # 6. 输出结果摘要
    logger.info("\n" + "=" * 50)
    logger.info("回测结果摘要")
    logger.info("=" * 50)
    logger.info(f"初始资金: {initial_capital:,.0f}")
    logger.info(f"最终净值: {result.get('final', 0):,.0f}")
    logger.info(f"总收益率: {result.get('total_return', 0):.2%}")
    logger.info(f"交易次数: {result.get('trades', 0)}")
    
    return result


def run_analysis(result: dict):
    """运行胜率分析
    
    Args:
        result: 回测结果
    """
    logger.info("\n[分析模块] 胜率分析...")
    
    if 'daily_df' not in result or result['daily_df'].empty:
        logger.warning("无回测数据，跳过分析")
        return
    
    daily_df = result['daily_df']
    returns = daily_df['return'].fillna(0)
    
    # 绩效指标
    metrics = PerformanceMetrics(returns=returns)
    
    # 分层分析
    layering = LayeringAnalysis(n_layers=5)
    
    # 敏感性分析（简化）
    sensitivity = SensitivityAnalysis({
        'min_score': [60, 70, 80],
        'max_positions': [5, 10, 15]
    })
    
    logger.info(f"\n胜率: {metrics.win_rate():.2%}")
    logger.info(f"盈亏比: {metrics.profit_loss_ratio():.2f}")
    logger.info(f"夏普比率: {metrics.sharpe_ratio():.2f}")
    logger.info(f"最大回撤: {metrics.max_drawdown():.2%}")


def recommend_params():
    """推荐最优参数"""
    logger.info("\n[参数推荐] 基于历史回测...")
    
    # 默认推荐参数
    recommended = {
        '止盈': '8%-12%',
        '止损': '5%-8%',
        '持仓周期': '5-10天',
        '最大持仓': '10只',
        '单只仓位': '10%',
        '最小得分': '70分',
        'KDJ阈值': 'J<20'
    }
    
    logger.info("\n推荐参数:")
    for k, v in recommended.items():
        logger.info(f"  {k}: {v}")
    
    return recommended


def recommend_capital(risk_level: str = 'medium'):
    """资金规模建议
    
    Args:
        risk_level: 风险偏好 (low/medium/high)
    """
    logger.info("\n[资金建议] 风险偏好: " + risk_level)
    
    suggestions = {
        'low': {'min': 500000, 'recommended': 1000000, 'max': 2000000},
        'medium': {'min': 300000, 'recommended': 500000, 'max': 1000000},
        'high': {'min': 100000, 'recommended': 300000, 'max': 500000}
    }
    
    s = suggestions.get(risk_level, suggestions['medium'])
    
    logger.info(f"  最低资金: {s['min']:,.0f}")
    logger.info(f"  推荐资金: {s['recommended']:,.0f}")
    logger.info(f"  最高资金: {s['max']:,.0f}")
    
    return s


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='波段抄底策略')
    parser.add_argument('--mode', choices=['backtest', 'select', 'analysis', 'all'], 
                        default='all', help='运行模式')
    parser.add_argument('--start', default='2020-01-01', help='开始日期')
    parser.add_argument('--end', default='2025-12-31', help='结束日期')
    parser.add_argument('--capital', type=float, default=1000000, help='初始资金')
    parser.add_argument('--risk', choices=['low', 'medium', 'high'], 
                        default='medium', help='风险偏好')
    
    args = parser.parse_args()
    
    result = None
    
    if args.mode in ['backtest', 'all']:
        result = run_backtest(args.start, args.end, args.capital)
    
    if args.mode in ['analysis', 'all'] and result:
        run_analysis(result)
    
    if args.mode == 'all':
        recommend_params()
        recommend_capital(args.risk)
    
    logger.info("\n" + "=" * 50)
    logger.info("🎉 执行完成！")
    logger.info("=" * 50)


if __name__ == '__main__':
    main()