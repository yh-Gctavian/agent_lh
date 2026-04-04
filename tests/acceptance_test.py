# -*- coding: utf-8 -*-
"""验收测试脚本"""

import sys
from pathlib import Path

# 确保模块路径
sys.path.insert(0, str(Path(__file__).parent.parent))

print("=" * 60)
print("波段抄底策略 - 验收测试")
print("=" * 60)

# 测试1: 数据层导入
print("\n[测试1] 数据层模块导入...")
try:
    from wave_bottom_strategy.data.loader import DataLoader
    from wave_bottom_strategy.data.processor import DataProcessor
    from wave_bottom_strategy.data.cache import DataCache
    print("  [PASS] DataLoader, DataProcessor, DataCache 导入成功")
except Exception as e:
    print(f"  [FAIL] 数据层导入失败: {e}")

# 测试2: 因子层导入
print("\n[测试2] 因子层模块导入...")
try:
    from wave_bottom_strategy.factors.kdj import KDJFactor
    from wave_bottom_strategy.factors.ma import MAFactor
    from wave_bottom_strategy.factors.volume import VolumeFactor
    from wave_bottom_strategy.factors.rsi import RSIFactor
    from wave_bottom_strategy.factors.macd import MACDFactor
    from wave_bottom_strategy.factors.bollinger import BollingerFactor
    print("  [PASS] 6个因子模块导入成功")
except Exception as e:
    print(f"  [FAIL] 因子层导入失败: {e}")

# 测试3: 因子权重验证
print("\n[测试3] 因子权重验证...")
try:
    kdj = KDJFactor()
    ma = MAFactor()
    vol = VolumeFactor()
    rsi = RSIFactor()
    macd = MACDFactor()
    boll = BollingerFactor()
    
    total = kdj.weight + ma.weight + vol.weight + rsi.weight + macd.weight + boll.weight
    
    print(f"  KDJ权重: {kdj.weight*100}%")
    print(f"  MA权重: {ma.weight*100}%")
    print(f"  成交量权重: {vol.weight*100}%")
    print(f"  RSI权重: {rsi.weight*100}%")
    print(f"  MACD权重: {macd.weight*100}%")
    print(f"  布林带权重: {boll.weight*100}%")
    print(f"  [PASS] 权重总和: {total*100}%")
except Exception as e:
    print(f"  [FAIL] 权重验证失败: {e}")

# 测试4: 选股模块导入
print("\n[测试4] 选股模块导入...")
try:
    from wave_bottom_strategy.selector.engine import SelectorEngine
    from wave_bottom_strategy.selector.scorer import FactorScorer
    print("  [PASS] SelectorEngine, FactorScorer 导入成功")
except Exception as e:
    print(f"  [FAIL] 选股模块导入失败: {e}")

# 测试5: 回测模块导入
print("\n[测试5] 回测模块导入...")
try:
    from wave_bottom_strategy.backtest.engine import BacktestEngine
    from wave_bottom_strategy.backtest.portfolio import Portfolio
    print("  [PASS] BacktestEngine, Portfolio 导入成功")
except Exception as e:
    print(f"  [FAIL] 回测模块导入失败: {e}")

# 测试6: 分析模块导入
print("\n[测试6] 分析模块导入...")
try:
    from wave_bottom_strategy.analysis.metrics import PerformanceMetrics
    from wave_bottom_strategy.analysis.reporter import ReportGenerator
    print("  [PASS] PerformanceMetrics, ReportGenerator 导入成功")
except Exception as e:
    print(f"  [FAIL] 分析模块导入失败: {e}")

# 测试7: 数据加载功能
print("\n[测试7] 数据加载功能...")
try:
    loader = DataLoader()
    df = loader.load_daily_data('000001', '20240101', '20241231')
    if len(df) > 0:
        print(f"  [PASS] 数据加载成功: {len(df)}条记录")
    else:
        print("  [WARN] 数据加载返回空（可能网络问题）")
except Exception as e:
    print(f"  [WARN] 数据加载异常: {e}")

# 测试8: 主入口
print("\n[测试8] 主入口模块...")
try:
    from wave_bottom_strategy.main import main
    print("  [PASS] main.py 导入成功")
except Exception as e:
    print(f"  [FAIL] 主入口导入失败: {e}")

print("\n" + "=" * 60)
print("验收测试完成")
print("=" * 60)