# -*- coding: utf-8 -*-
"""波段抄底策略主入口"""

import argparse
from pathlib import Path
from datetime import datetime

from config import settings, FACTOR_PARAMS, SELECTOR_PARAMS
from data.loader import DataLoader
from data.processor import DataProcessor
from data.cache import DataCache
from selector.engine import SelectorEngine
from backtest.engine import BacktestEngine
from analysis.metrics import PerformanceMetrics
from analysis.reporter import ReportGenerator
from utils.logger import get_logger

logger = get_logger('wave_bottom', settings.log_level, settings.log_file)


def run_backtest(start_date: str, end_date: str, initial_capital: float = 1000000.0):
    """运行回测
    
    Args:
        start_date: 开始日期 (YYYY-MM-DD)
        end_date: 结束日期 (YYYY-MM-DD)
        initial_capital: 初始资金
    """
    logger.info(f"开始回测: {start_date} -> {end_date}")
    logger.info(f"初始资金: {initial_capital:,.0f}")
    
    # 初始化组件
    engine = BacktestEngine(
        initial_capital=initial_capital,
        max_positions=SELECTOR_PARAMS.get('max_positions', 10)
    )
    
    # 运行回测
    result = engine.run(
        start_date=start_date,
        end_date=end_date,
        stock_pool=None  # 使用默认沪深300
    )
    
    if 'error' in result:
        logger.error(f"回测失败: {result['error']}")
        return
    
    # 计算绩效指标
    daily_df = result.get('daily_df')
    if daily_df is not None and not daily_df.empty:
        metrics = PerformanceMetrics(returns=daily_df['return'])
        metrics_dict = metrics.get_all_metrics()
        
        # 打印结果
        logger.info("\n" + "="*50)
        logger.info("回测结果:")
        logger.info(f"  初始资金: {result['initial']:,.0f}")
        logger.info(f"  最终净值: {result['final']:,.0f}")
        logger.info(f"  总收益率: {result['total_return']:.2%}")
        logger.info(f"  交易次数: {result['trades']}")
        logger.info("")
        logger.info("绩效指标:")
        logger.info(f"  夏普比率: {metrics_dict['sharpe_ratio']:.2f}")
        logger.info(f"  最大回撤: {metrics_dict['max_drawdown']:.2%}")
        logger.info(f"  年化收益: {metrics_dict['annual_return']:.2%}")
        logger.info("="*50)
        
        # 生成报告
        reporter = ReportGenerator()
        report_path = reporter.generate(
            metrics=metrics_dict,
            backtest_result=result
        )
        logger.info(f"报告已生成: {report_path}")
    
    logger.info("回测完成")
    return result


def run_select(trade_date: str, top_n: int = 10):
    """执行选股
    
    Args:
        trade_date: 交易日期 (YYYY-MM-DD)
        top_n: 返回数量
    """
    logger.info(f"执行选股: {trade_date}")
    
    selector = SelectorEngine()
    
    from datetime import datetime
    dt = datetime.strptime(trade_date, '%Y-%m-%d').date()
    
    result = selector.run(
        trade_date=dt,
        stock_pool=None,
        top_n=top_n,
        min_score=SELECTOR_PARAMS.get('min_score', 60)
    )
    
    if result.empty:
        logger.warning("无选股结果")
        return
    
    logger.info(f"\n选股结果 (Top {top_n}):")
    logger.info("-"*60)
    
    for i, row in result.iterrows():
        logger.info(f"  {row.get('ts_code', 'N/A')}: 得分 {row.get('total_score', 0):.2f}")
    
    return result


def test_factor_calculation(symbol: str = '000001'):
    """测试因子计算
    
    Args:
        symbol: 股票代码
    """
    logger.info(f"测试因子计算: {symbol}")
    
    # 加载数据
    loader = DataLoader()
    df = loader.load_daily_data(symbol, '20200101', '20251231', 'qfq')
    
    if df.empty:
        logger.error("数据加载失败")
        return
    
    logger.info(f"数据加载成功: {len(df)}条")
    
    # 计算因子
    from selector.scorer import FactorScorer
    scorer = FactorScorer()
    
    scores = scorer.score_stock(df)
    
    logger.info(f"\n最新因子得分:")
    for col in scores.columns:
        if 'score' in col:
            logger.info(f"  {col}: {scores[col].iloc[-1]:.2f}")
    
    return scores


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='波段抄底策略',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 运行回测
  python main.py --mode backtest --start 2020-01-01 --end 2025-12-31
  
  # 执行选股
  python main.py --mode select --date 2025-01-15 --top 10
  
  # 测试因子
  python main.py --mode test_factor --symbol 000001
        """
    )
    
    parser.add_argument(
        '--mode',
        choices=['backtest', 'select', 'test_factor'],
        default='backtest',
        help='运行模式'
    )
    parser.add_argument(
        '--start',
        default=settings.backtest_start,
        help='开始日期 (YYYY-MM-DD)'
    )
    parser.add_argument(
        '--end',
        default=settings.backtest_end,
        help='结束日期 (YYYY-MM-DD)'
    )
    parser.add_argument(
        '--capital',
        type=float,
        default=1000000.0,
        help='初始资金'
    )
    parser.add_argument(
        '--date',
        help='选股日期 (YYYY-MM-DD)'
    )
    parser.add_argument(
        '--top',
        type=int,
        default=10,
        help='选股数量'
    )
    parser.add_argument(
        '--symbol',
        default='000001',
        help='股票代码（测试用）'
    )
    
    args = parser.parse_args()
    
    if args.mode == 'backtest':
        run_backtest(args.start, args.end, args.capital)
    
    elif args.mode == 'select':
        if not args.date:
            args.date = datetime.now().strftime('%Y-%m-%d')
        run_select(args.date, args.top)
    
    elif args.mode == 'test_factor':
        test_factor_calculation(args.symbol)


if __name__ == '__main__':
    main()