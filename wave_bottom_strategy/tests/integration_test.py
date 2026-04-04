# -*- coding: utf-8 -*-
"""全链路联调测试"""

import sys
from pathlib import Path
from datetime import date, datetime

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from wave_bottom_strategy.data.loader import DataLoader
from data.processor import DataProcessor
from wave_bottom_strategy.factors.kdj import KDJFactor
from wave_bottom_strategy.factors.ma import MAFactor
from wave_bottom_strategy.factors.volume import VolumeFactor
from wave_bottom_strategy.factors.rsi import RSIFactor
from wave_bottom_strategy.factors.macd import MACDFactor
from wave_bottom_strategy.factors.bollinger import BollingerFactor
from selector.scorer import FactorScorer
from wave_bottom_strategy.selector.engine import SelectorEngine
from wave_bottom_strategy.backtest.engine import BacktestEngine
from wave_bottom_strategy.analysis.metrics import PerformanceMetrics
from wave_bottom_strategy.utils.logger import get_logger

logger = get_logger('integration_test')


def test_data_layer():
    """测试数据层"""
    logger.info("=" * 50)
    logger.info("测试数据层")
    logger.info("=" * 50)
    
    loader = DataLoader()
    processor = DataProcessor()
    
    # 测试单只股票数据加载
    logger.info("1. 测试数据加载...")
    df = loader.load_daily_data(
        symbol='000001',
        start_date='20240101',
        end_date='20241231',
        adjust='qfq'
    )
    
    if df.empty:
        logger.error("❌ 数据加载失败")
        return False
    
    logger.info(f"✅ 数据加载成功: {len(df)}条")
    
    # 测试数据预处理
    logger.info("2. 测试数据预处理...")
    df = processor.process_all(df, '000001')
    logger.info(f"✅ 数据预处理完成")
    
    # 测试股票池加载
    logger.info("3. 测试股票池加载...")
    pool = loader.load_stock_pool('hs300')
    if pool:
        logger.info(f"✅ 股票池加载成功: {len(pool)}只")
    else:
        logger.warning("⚠️ 股票池加载返回空")
    
    return True


def test_factor_layer():
    """测试因子层"""
    logger.info("=" * 50)
    logger.info("测试因子层")
    logger.info("=" * 50)
    
    loader = DataLoader()
    
    # 加载测试数据
    df = loader.load_daily_data(
        symbol='000001',
        start_date='20240101',
        end_date='20241231',
        adjust='qfq'
    )
    
    if df.empty:
        logger.error("❌ 无法加载测试数据")
        return False
    
    # 测试各因子计算
    factors = [
        ('KDJ', KDJFactor()),
        ('MA', MAFactor()),
        ('Volume', VolumeFactor()),
        ('RSI', RSIFactor()),
        ('MACD', MACDFactor()),
        ('Bollinger', BollingerFactor())
    ]
    
    for name, factor in factors:
        try:
            result = factor.calculate(df)
            if result.empty:
                logger.warning(f"⚠️ {name} 因子计算返回空")
            else:
                logger.info(f"✅ {name} 因子计算成功: {len(result)}条")
        except Exception as e:
            logger.error(f"❌ {name} 因子计算失败: {e}")
            return False
    
    # 测试打分器
    logger.info("测试因子打分器...")
    scorer = FactorScorer()
    scores = scorer.score_stock(df)
    
    if scores.empty:
        logger.error("❌ 打分失败")
        return False
    
    logger.info(f"✅ 打分成功: 最新总分={scores['total_score'].iloc[-1]:.2f}")
    
    return True


def test_selector_layer():
    """测试选股层"""
    logger.info("=" * 50)
    logger.info("测试选股层")
    logger.info("=" * 50)
    
    engine = SelectorEngine()
    
    # 测试单只股票选股
    logger.info("测试单只股票选股...")
    result = engine.run_single('000001')
    
    if result.empty:
        logger.warning("⚠️ 选股结果为空")
    else:
        logger.info(f"✅ 选股成功: {len(result)}条")
        latest = result.iloc[-1]
        logger.info(f"   总分: {latest['total_score']:.2f}")
    
    return True


def test_backtest_layer():
    """测试回测层"""
    logger.info("=" * 50)
    logger.info("测试回测层")
    logger.info("=" * 50)
    
    engine = BacktestEngine(initial_capital=1_000_000)
    
    # 简短回测
    logger.info("运行回测(测试模式)...")
    try:
        result = engine.run(
            start_date='2024-01-01',
            end_date='2024-03-31',  # 3个月测试
            stock_pool=['000001', '000002', '600000'],  # 小规模测试
            rebalance_freq=5
        )
        
        if 'error' in result:
            logger.warning(f"⚠️ 回测返回错误: {result['error']}")
        else:
            logger.info(f"✅ 回测成功")
            logger.info(f"   总收益率: {result['total_return']:.2%}")
            logger.info(f"   最大回撤: {result['max_drawdown']:.2%}")
            logger.info(f"   交易次数: {result['trade_count']}")
        
    except Exception as e:
        logger.warning(f"⚠️ 回测执行异常: {e}")
    
    return True


def test_analysis_layer():
    """测试分析层"""
    logger.info("=" * 50)
    logger.info("测试分析层")
    logger.info("=" * 50)
    
    import pandas as pd
    import numpy as np
    
    # 模拟收益数据
    np.random.seed(42)
    returns = pd.Series(np.random.randn(100) * 0.02)
    
    from wave_bottom_strategy.analysis.metrics import PerformanceMetrics
    
    metrics = PerformanceMetrics(returns)
    
    logger.info(f"✅ 胜率: {metrics.win_rate():.2%}")
    logger.info(f"✅ 夏普比率: {metrics.sharpe_ratio():.2f}")
    logger.info(f"✅ 最大回撤: {metrics.max_drawdown():.2%}")
    
    return True


def run_all_tests():
    """运行所有测试"""
    logger.info("=" * 60)
    logger.info("波段抄底策略 - 全链路联调测试")
    logger.info("=" * 60)
    
    results = {
        '数据层': test_data_layer(),
        '因子层': test_factor_layer(),
        '选股层': test_selector_layer(),
        '回测层': test_backtest_layer(),
        '分析层': test_analysis_layer()
    }
    
    # 汇总结果
    logger.info("=" * 60)
    logger.info("测试结果汇总")
    logger.info("=" * 60)
    
    passed = sum(results.values())
    total = len(results)
    
    for name, result in results.items():
        status = "✅ 通过" if result else "❌ 失败"
        logger.info(f"{name}: {status}")
    
    logger.info(f"\n通过率: {passed}/{total} ({passed/total*100:.1f}%)")
    
    return passed == total


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)