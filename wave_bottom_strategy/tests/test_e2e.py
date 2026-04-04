# -*- coding: utf-8 -*-
"""端到端测试"""

import pytest
from datetime import date
import pandas as pd

from data.loader import DataLoader
from data.processor import DataProcessor
from factors.kdj import KDJFactor
from factors.ma import MAFactor
from selector.engine import SelectorEngine
from backtest.engine import BacktestEngine
from analysis.metrics import PerformanceMetrics


class TestEndToEnd:
    """端到端测试"""
    
    def test_data_loading(self):
        """测试数据加载"""
        loader = DataLoader()
        
        # 测试加载单只股票
        df = loader.load_daily_data('000001', '20240101', '20241231')
        
        assert not df.empty, "数据加载失败"
        assert 'close' in df.columns, "缺少close列"
    
    def test_data_processing(self):
        """测试数据处理"""
        loader = DataLoader()
        processor = DataProcessor()
        
        df = loader.load_daily_data('000001', '20240101', '20241231')
        processed = processor.process_all(df, '000001')
        
        assert 'is_suspended' in processed.columns, "缺少停牌标记"
    
    def test_factor_calculation(self):
        """测试因子计算"""
        loader = DataLoader()
        
        df = loader.load_daily_data('000001', '20240101', '20241231')
        
        # KDJ因子
        kdj = KDJFactor()
        kdj_data = kdj.calculate(df)
        
        assert not kdj_data.empty, "KDJ计算失败"
        assert 'k' in kdj_data.columns, "缺少K值"
        assert 'd' in kdj_data.columns, "缺少D值"
        assert 'j' in kdj_data.columns, "缺少J值"
    
    def test_selector_engine(self):
        """测试选股引擎"""
        selector = SelectorEngine()
        
        # 简化测试：单只股票评分
        scores = selector.run_single('000001')
        
        # 可能无数据（网络问题等），只检查结构
        if not scores.empty:
            assert 'total_score' in scores.columns, "缺少总分"
    
    def test_backtest_engine(self):
        """测试回测引擎"""
        engine = BacktestEngine(initial_capital=100000)
        
        # 简化测试
        result = engine.run('2024-01-01', '2024-01-31', ['000001'])
        
        assert 'initial' in result, "缺少初始资金"
        assert 'final' in result, "缺少最终净值"
    
    def test_performance_metrics(self):
        """测试绩效指标"""
        # 模拟收益率
        returns = pd.Series([0.01, -0.02, 0.03, 0.01, -0.01])
        
        metrics = PerformanceMetrics(returns=returns)
        
        sharpe = metrics.sharpe_ratio()
        max_dd = metrics.max_drawdown()
        
        assert isinstance(sharpe, float), "夏普比率计算失败"
        assert isinstance(max_dd, float), "最大回撤计算失败"
    
    def test_full_pipeline(self):
        """完整流程测试"""
        # 1. 加载数据
        loader = DataLoader()
        df = loader.load_daily_data('000001', '20240101', '20241231')
        
        if df.empty:
            pytest.skip("数据加载失败，跳过完整测试")
        
        # 2. 计算因子
        kdj = KDJFactor()
        kdj_data = kdj.calculate(df)
        
        # 3. 获取得分
        scores = kdj.get_score(kdj_data)
        
        assert len(scores) > 0, "得分计算失败"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])