# -*- coding: utf-8 -*-
"""M6联调测试 - 端到端流程验证"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from datetime import datetime, date
import pandas as pd

from wave_bottom_strategy.data.loader import DataLoader
from wave_bottom_strategy.data.processor import DataProcessor
from wave_bottom_strategy.factors.kdj import KDJFactor
from wave_bottom_strategy.factors.ma import MAFactor
from wave_bottom_strategy.factors.volume import VolumeFactor
from wave_bottom_strategy.selector.engine import SelectorEngine
from wave_bottom_strategy.backtest.engine import BacktestEngine
from wave_bottom_strategy.analysis.metrics import PerformanceMetrics
from wave_bottom_strategy.analysis.reporter import ReportGenerator


def test_data_layer():
    """测试数据层"""
    print("\n" + "="*50)
    print("测试数据层")
    print("="*50)
    
    loader = DataLoader()
    
    # 测试加载股票池
    print("加载沪深300股票池...")
    try:
        pool = loader.load_stock_pool('hs300')
        print(f"✅ 股票池加载成功: {len(pool)}只")
    except Exception as e:
        print(f"❌ 股票池加载失败: {e}")
        pool = []
    
    return pool


def test_factor_calculation(symbol: str = '000001'):
    """测试因子计算"""
    print("\n" + "="*50)
    print("测试因子计算")
    print("="*50)
    
    loader = DataLoader()
    
    # 加载数据
    print(f"加载{symbol}日K线数据...")
    try:
        df = loader.load_daily_data(symbol, '20240101', '20250331', 'qfq')
        print(f"✅ 数据加载成功: {len(df)}条")
    except Exception as e:
        print(f"❌ 数据加载失败: {e}")
        return None
    
    # 计算因子
    factors = {
        'KDJ': KDJFactor(),
        'MA': MAFactor(),
        'Volume': VolumeFactor()
    }
    
    for name, factor in factors.items():
        try:
            result = factor.calculate(df.tail(100))
            print(f"✅ {name}因子计算成功")
        except Exception as e:
            print(f"❌ {name}因子计算失败: {e}")
    
    return df


def test_selector():
    """测试选股引擎"""
    print("\n" + "="*50)
    print("测试选股引擎")
    print("="*50)
    
    selector = SelectorEngine()
    
    try:
        result = selector.run(
            trade_date=date(2025, 3, 28),
            top_n=5,
            min_score=60.0
        )
        print(f"✅ 选股完成: {len(result)}只")
        if not result.empty:
            print(result.head())
    except Exception as e:
        print(f"❌ 选股失败: {e}")


def test_backtest():
    """测试回测"""
    print("\n" + "="*50)
    print("测试回测框架")
    print("="*50)
    
    engine = BacktestEngine(initial_capital=1000000)
    
    try:
        result = engine.run('2024-01-01', '2024-03-31')
        print(f"✅ 回测完成")
        if result:
            print(f"  - 最终资金: {result.get('final', 0):,.2f}")
            print(f"  - 总收益: {result.get('total_return', 0)*100:.2f}%")
            print(f"  - 交易次数: {result.get('trades', 0)}")
    except Exception as e:
        print(f"❌ 回测失败: {e}")


def test_analysis():
    """测试分析模块"""
    print("\n" + "="*50)
    print("测试分析模块")
    print("="*50)
    
    # 模拟收益序列
    import numpy as np
    np.random.seed(42)
    returns = pd.Series(np.random.normal(0.001, 0.02, 100))
    
    metrics = PerformanceMetrics(returns)
    all_metrics = metrics.get_all_metrics()
    
    print("✅ 绩效指标计算完成:")
    for k, v in all_metrics.items():
        print(f"  - {k}: {v}")


def run_full_test():
    """运行完整测试"""
    print("\n" + "="*60)
    print("波段抄底策略 - M6联调测试")
    print("="*60)
    
    # 1. 数据层测试
    pool = test_data_layer()
    
    # 2. 因子测试
    if pool:
        symbol = pool[0] if len(pool) > 0 else '000001'
    else:
        symbol = '000001'
    df = test_factor_calculation(symbol)
    
    # 3. 选股测试
    test_selector()
    
    # 4. 回测测试
    test_backtest()
    
    # 5. 分析测试
    test_analysis()
    
    print("\n" + "="*60)
    print("M6联调测试完成")
    print("="*60)


if __name__ == '__main__':
    run_full_test()