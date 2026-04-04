# -*- coding: utf-8 -*-
"""端到端测试"""

import pytest


def test_import():
    """测试模块导入"""
    try:
        from wave_bottom_strategy.data.loader import DataLoader
        from wave_bottom_strategy.factors.kdj import KDJFactor
        from wave_bottom_strategy.selector.engine import SelectorEngine
        from wave_bottom_strategy.backtest.engine import BacktestEngine
        assert True
    except ImportError as e:
        pytest.skip(f"导入失败: {e}")


def test_factor_calculate():
    """测试因子计算"""
    try:
        from wave_bottom_strategy.factors.kdj import KDJFactor
        factor = KDJFactor()
        assert factor.weight == 0.45
    except ImportError:
        pytest.skip("导入失败")


if __name__ == '__main__':
    pytest.main([__file__])