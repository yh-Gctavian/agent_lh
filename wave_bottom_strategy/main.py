# -*- coding: utf-8 -*-
"""Wave Bottom Strategy - Main Entry Point

波段抄底策略主入口

功能：
1. 数据加载验证
2. 选股引擎运行
3. 回测执行
4. 结果分析
"""

import argparse
import logging
from pathlib import Path
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_data_loader():
    """测试数据加载器"""
    logger.info("=== 测试数据加载器 ===")
    
    from wave_bottom_strategy.data.loader import DataLoader
    
    loader = DataLoader(source_mode='hybrid')
    
    # 测试加载单只股票
    df = loader.load_daily_data('600000', '20240101', '20240131')
    
    if not df.empty:
        logger.info(f"数据加载成功: {len(df)}条")
        logger.info(f"列名: {df.columns.tolist()}")
        logger.info(f"最新数据: {df.tail(1).to_dict('records')}")
    else:
        logger.warning("数据加载失败")
    
    # 统计信息
    stats = loader.get_stats()
    logger.info(f"统计: {stats}")
    
    return df


def test_tdx_loader():
    """测试通达信数据加载"""
    logger.info("=== 测试通达信数据加载 ===")
    
    from data.tdx_loader import TdxLocalLoader
    
    loader = TdxLocalLoader()
    
    # 测试路径
    logger.info(f"通达信路径: {loader.VIPDOC_DIR}")
    logger.info(f"路径存在: {loader.VIPDOC_DIR.exists()}")
    
    # 测试数据覆盖
    coverage = loader.get_data_coverage('600000')
    logger.info(f"600000数据覆盖: {coverage}")
    
    # 测试加载
    df = loader.load_daily_data('600000', '20240101', '20241231')
    
    if not df.empty:
        logger.info(f"通达信数据: {len(df)}条")
    else:
        logger.warning("通达信数据加载失败")
    
    return df


def test_selector():
    """测试选股引擎"""
    logger.info("=== 测试选股引擎 ===")
    
    from wave_bottom_strategy.selector.engine import SelectorEngine
    from wave_bottom_strategy.data.loader import DataLoader
    
    loader = DataLoader(source_mode='hybrid')
    selector = SelectorEngine(data_loader=loader)
    
    # 加载股票池
    stock_pool = loader.load_stock_pool('hs300')[:20]  # 测试用少量股票
    
    if not stock_pool:
        logger.warning("股票池加载失败，使用默认测试股票")
        stock_pool = ['600000', '000001', '600519', '000002', '600036']
    
    # 执行选股
    result = selector.run(stock_pool, '20240115')
    
    if not result.empty:
        logger.info(f"选股结果: {len(result)}只")
        logger.info(f"Top 5: {result.head(5).to_dict('records')}")
    else:
        logger.warning("选股失败")
    
    return result


def run_backtest(
    start: str = '2020-01-01',
    end: str = '2025-12-31',
    stock_pool: str = 'hs300',
    initial_capital: float = 1_000_000.0,
    save_result: bool = True
):
    """运行回测
    
    Args:
        start: 开始日期
        end: 结束日期
        stock_pool: 股票池名称
        initial_capital: 初始资金
        save_result: 是否保存结果
    """
    logger.info(f"=== 运行回测: {start} -> {end} ===")
    
    from wave_bottom_strategy.backtest.engine import BacktestEngine, BacktestResult
    from wave_bottom_strategy.data.loader import DataLoader
    
    # 初始化
    loader = DataLoader(source_mode='hybrid')
    
    # 加载股票池
    stocks = loader.load_stock_pool(stock_pool)
    
    if not stocks:
        logger.warning(f"股票池加载失败: {stock_pool}")
        return None
    
    logger.info(f"股票池: {len(stocks)}只股票")
    
    # 创建回测引擎
    engine = BacktestEngine(
        initial_capital=initial_capital,
        data_loader=loader
    )
    
    # 运行回测
    result = engine.run(
        start_date=start,
        end_date=end,
        stock_pool=stocks[:50],  # 测试用前50只
        save_result=save_result
    )
    
    # 输出结果
    if result.metrics:
        logger.info("=" * 50)
        logger.info("回测结果摘要:")
        logger.info(f"累计收益率: {result.metrics.get('cumulative_return', 0)*100:.2f}%")
        logger.info(f"年化收益率: {result.metrics.get('annualized_return', 0)*100:.2f}%")
        logger.info(f"夏普比率: {result.metrics.get('sharpe_ratio', 0):.2f}")
        logger.info(f"最大回撤: {result.metrics.get('max_drawdown', 0)*100:.2f}%")
        logger.info(f"总交易数: {result.metrics.get('trade_stats', {}).get('total_trades', 0)}")
        logger.info("=" * 50)
    
    return result


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='波段抄底策略选股系统')
    
    parser.add_argument('--mode', choices=['test', 'backtest', 'select'],
                       default='test', help='运行模式')
    parser.add_argument('--start', default='2024-01-01', help='开始日期')
    parser.add_argument('--end', default='2024-12-31', help='结束日期')
    parser.add_argument('--pool', default='hs300', help='股票池')
    parser.add_argument('--capital', type=float, default=1000000.0, help='初始资金')
    
    args = parser.parse_args()
    
    if args.mode == 'test':
        # 测试模式：验证各模块
        test_data_loader()
        test_tdx_loader()
        test_selector()
        
    elif args.mode == 'backtest':
        # 回测模式
        run_backtest(args.start, args.end, args.pool, args.capital)
        
    elif args.mode == 'select':
        # 选股模式
        test_selector()
    
    logger.info("完成")


if __name__ == '__main__':
    main()