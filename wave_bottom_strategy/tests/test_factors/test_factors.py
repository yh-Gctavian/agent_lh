# -*- coding: utf-8 -*-
"""因子模块测试"""

import pytest
import pandas as pd
import numpy as np

from factors.kdj import KDJFactor
from factors.ma import MAFactor
from factors.volume import VolumeFactor
from factors.rsi import RSIFactor
from factors.macd import MACDFactor
from factors.bollinger import BollingerFactor


class TestKDJFactor:
    """KDJ因子测试"""
    
    @pytest.fixture
    def sample_data(self):
        """生成测试数据"""
        np.random.seed(42)
        n = 100
        return pd.DataFrame({
            'trade_date': pd.date_range('2020-01-01', periods=n),
            'open': 10 + np.random.randn(n).cumsum(),
            'high': 11 + np.random.randn(n).cumsum(),
            'low': 9 + np.random.randn(n).cumsum(),
            'close': 10 + np.random.randn(n).cumsum(),
            'volume': np.random.randint(100000, 1000000, n)
        })
    
    def test_kdj_calculate(self, sample_data):
        """测试KDJ计算"""
        factor = KDJFactor()
        result = factor.calculate(sample_data)
        
        assert 'k' in result.columns
        assert 'd' in result.columns
        assert 'j' in result.columns
    
    def test_kdj_score(self, sample_data):
        """测试KDJ评分"""
        factor = KDJFactor()
        kdj_data = factor.calculate(sample_data)
        scores = factor.get_score(kdj_data)
        
        assert scores.max() <= 100
        assert scores.min() >= 0
    
    def test_kdj_weight(self):
        """测试KDJ权重"""
        factor = KDJFactor()
        assert factor.weight == 0.45


class TestMAFactor:
    """均线因子测试"""
    
    @pytest.fixture
    def sample_data(self):
        np.random.seed(42)
        n = 100
        return pd.DataFrame({
            'trade_date': pd.date_range('2020-01-01', periods=n),
            'close': 10 + np.random.randn(n).cumsum(),
            'high': 11 + np.random.randn(n).cumsum(),
            'low': 9 + np.random.randn(n).cumsum(),
            'volume': np.random.randint(100000, 1000000, n)
        })
    
    def test_ma_calculate(self, sample_data):
        factor = MAFactor()
        result = factor.calculate(sample_data)
        
        assert 'ma5' in result.columns
        assert 'ma20' in result.columns
        assert 'ma60' in result.columns
    
    def test_ma_weight(self):
        factor = MAFactor()
        assert factor.weight == 0.15


class TestVolumeFactor:
    """成交量因子测�?""
    
    @pytest.fixture
    def sample_data(self):
        np.random.seed(42)
        n = 100
        return pd.DataFrame({
            'trade_date': pd.date_range('2020-01-01', periods=n),
            'volume': np.random.randint(100000, 1000000, n),
            'close': 10 + np.random.randn(n).cumsum(),
            'high': 11 + np.random.randn(n).cumsum(),
            'low': 9 + np.random.randn(n).cumsum()
        })
    
    def test_volume_calculate(self, sample_data):
        factor = VolumeFactor()
        result = factor.calculate(sample_data)
        
        assert 'vol_ratio' in result.columns
        assert 'low_vol_days' in result.columns
    
    def test_volume_weight(self):
        factor = VolumeFactor()
        assert factor.weight == 0.15


class TestRSIFactor:
    """RSI因子测试"""
    
    @pytest.fixture
    def sample_data(self):
        np.random.seed(42)
        n = 100
        return pd.DataFrame({
            'trade_date': pd.date_range('2020-01-01', periods=n),
            'close': 10 + np.random.randn(n).cumsum()
        })
    
    def test_rsi_calculate(self, sample_data):
        factor = RSIFactor()
        result = factor.calculate(sample_data)
        
        assert 'rsi' in result.columns
    
    def test_rsi_weight(self):
        factor = RSIFactor()
        assert factor.weight == 0.10


class TestMACDFactor:
    """MACD因子测试"""
    
    @pytest.fixture
    def sample_data(self):
        np.random.seed(42)
        n = 100
        return pd.DataFrame({
            'trade_date': pd.date_range('2020-01-01', periods=n),
            'close': 10 + np.random.randn(n).cumsum()
        })
    
    def test_macd_calculate(self, sample_data):
        factor = MACDFactor()
        result = factor.calculate(sample_data)
        
        assert 'dif' in result.columns
        assert 'dea' in result.columns
        assert 'macd' in result.columns
    
    def test_macd_weight(self):
        factor = MACDFactor()
        assert factor.weight == 0.10


class TestBollingerFactor:
    """布林带因子测�?""
    
    @pytest.fixture
    def sample_data(self):
        np.random.seed(42)
        n = 100
        return pd.DataFrame({
            'trade_date': pd.date_range('2020-01-01', periods=n),
            'close': 10 + np.random.randn(n).cumsum()
        })
    
    def test_bollinger_calculate(self, sample_data):
        factor = BollingerFactor()
        result = factor.calculate(sample_data)
        
        assert 'upper' in result.columns
        assert 'mid' in result.columns
        assert 'lower' in result.columns
        assert 'bb_pos' in result.columns
    
    def test_bollinger_weight(self):
        factor = BollingerFactor()
        assert factor.weight == 0.05
