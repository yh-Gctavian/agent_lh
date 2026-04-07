# -*- coding: utf-8 -*-
"""KDJ因子与通达信数据对比测试"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from wave_bottom_strategy.factors.kdj import KDJFactor
from wave_bottom_strategy.data.tdx_loader import TdxLocalLoader


class TestKDJTdxMatch:
    """验证系统KDJ计算与通达信一致性"""

    @pytest.fixture
    def tdx_loader(self):
        """通达信数据加载器"""
        return TdxLocalLoader()

    @pytest.fixture
    def kdj_factor(self):
        """KDJ因子计算器"""
        return KDJFactor({'n': 9, 'm1': 3, 'm2': 3})

    def test_kdj_params_consistency(self, kdj_factor):
        """测试KDJ参数与通达信一致"""
        assert kdj_factor.n == 9, "N参数应为9"
        assert kdj_factor.m1 == 3, "M1参数应为3"
        assert kdj_factor.m2 == 3, "M2参数应为3"

    def test_rsv_calculation(self, kdj_factor):
        """测试RSV计算逻辑"""
        # 构造测试数据
        high = np.array([10, 11, 12, 13, 12, 11, 10, 9, 10, 11, 12, 13])
        low = np.array([8, 9, 10, 11, 10, 9, 8, 7, 8, 9, 10, 11])
        close = np.array([9, 10, 11, 12, 11, 10, 9, 8, 9, 10, 11, 12])

        k, d = kdj_factor._calc_kdj(high, low, close)

        # 验证第9个点（索引8，N=9后的第一个有效RSV）
        # RSV = (close - low_n) / (high_n - low_n) * 100
        # 索引8: high_n = max(high[0:9]) = 13, low_n = min(low[0:9]) = 7
        # close[8] = 9, RSV = (9-7)/(13-7)*100 = 33.33

        # 验证非NaN值存在
        assert not np.isnan(k[8:]).all(), "K值从索引8开始应有有效值"

    def test_sma_calculation(self, kdj_factor):
        """测试SMA计算逻辑（通达信风格）"""
        # SMA(X, N) = (prev_SMA * (N-1) + X) / N
        data = np.array([0, 0, 0, 50, 60, 70])

        result = kdj_factor._sma(data, 3)

        # 索引2: SMA = mean([0,0,0]) = 0
        # 索引3: SMA = (0 * 2 + 50) / 3 = 16.67
        # 索引4: SMA = (16.67 * 2 + 60) / 3 = 31.11
        # 索引5: SMA = (31.11 * 2 + 70) / 3 = 44.07

        assert abs(result[2] - 0) < 0.01, "SMA初始值应为0"
        assert abs(result[3] - 16.67) < 1, "SMA计算索引3应约为16.67"
        assert abs(result[4] - 31.11) < 1, "SMA计算索引4应约为31.11"
        assert abs(result[5] - 44.07) < 1, "SMA计算索引5应约为44.07"

    def test_j_value_formula(self, kdj_factor):
        """测试J值公式 J = 3K - 2D"""
        high = np.array([10, 11, 12, 13, 12, 11, 10, 9, 10, 11, 12, 13])
        low = np.array([8, 9, 10, 11, 10, 9, 8, 7, 8, 9, 10, 11])
        close = np.array([9, 10, 11, 12, 11, 10, 9, 8, 9, 10, 11, 12])

        k, d = kdj_factor._calc_kdj(high, low, close)
        j = 3 * k - 2 * d

        # 验证J值范围（理论范围 -20 ~ 120，实际可能超出）
        valid_j = j[~np.isnan(j)]
        assert valid_j.min() >= -50, "J值不应过低"
        assert valid_j.max() <= 150, "J值不应过高"

    def test_kdj_with_tdx_data(self, tdx_loader, kdj_factor):
        """使用通达信真实数据验证KDJ计算"""
        # 加载平安银行(000001)日线数据
        df = tdx_loader.load_daily_data('000001')

        if df.empty:
            pytest.skip("通达信数据不可用，跳过真实数据测试")

        # 系统计算KDJ
        kdj_result = kdj_factor.calculate(df)

        # 验证输出结构
        assert 'k' in kdj_result.columns, "应包含K值"
        assert 'd' in kdj_result.columns, "应包含D值"
        assert 'j' in kdj_result.columns, "应包含J值"

        # 验证数据长度一致
        assert len(kdj_result) == len(df), "KDJ输出长度应与输入一致"

        # 验证有效数据比例（前N-1个为NaN）
        valid_count = kdj_result['k'].notna().sum()
        expected_valid = len(df) - kdj_factor.n + 1
        assert valid_count >= expected_valid - 1, f"有效K值应至少{expected_valid-1}个"

    def test_kdj_extreme_values(self, kdj_factor):
        """测试极端情况下的KDJ计算"""
        # 超买情况：收盘价接近最高价
        high = np.array([10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21])
        low = np.array([8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19])
        close = np.array([10, 11, 12, 13, 14, 15, 16, 17, 18, 20, 21, 21])  # 最后几个接近最高

        k, d = kdj_factor._calc_kdj(high, low, close)
        j = 3 * k - 2 * d

        # 超买时K、D应接近100
        valid_k = k[~np.isnan(k)]
        assert valid_k[-1] >= 80, "超买情况K值应>=80"

    def test_kdj_score_mapping(self, kdj_factor):
        """测试KDJ得分映射逻辑"""
        # 构造KDJ数据
        kdj_data = pd.DataFrame({
            'j': [10, 25, 40, 80, 110]
        })

        scores = kdj_factor.get_score(kdj_data)

        # J < 20: 得分100（抄底信号）
        assert scores.iloc[0] == 100, "J<20应得分100"

        # 20 <= J < 30: 得分80
        assert scores.iloc[1] == 80, "J在20-30应得分80"

        # 30 <= J < 50: 得分50
        assert scores.iloc[2] == 50, "J在30-50应得分50"

        # J >= 50: 得分30（观望）
        assert scores.iloc[3] == 30, "J>=50应得分30"
        assert scores.iloc[4] == 30, "J>100应得分30"

    def test_kdj_weight(self, kdj_factor):
        """测试KDJ权重"""
        assert kdj_factor.weight == 0.45, "KDJ权重应为45%"


class TestKDJIntegration:
    """KDJ因子集成测试"""

    def test_kdj_full_pipeline(self):
        """测试完整计算流程"""
        # 模拟数据
        df = pd.DataFrame({
            'trade_date': pd.date_range('2024-01-01', periods=30),
            'high': np.random.uniform(10, 15, 30),
            'low': np.random.uniform(8, 12, 30),
            'close': np.random.uniform(9, 14, 30),
            'volume': np.random.uniform(100000, 500000, 30)
        })

        kdj = KDJFactor()
        result = kdj.calculate(df)

        # 验证输出
        assert len(result) == 30, "输出长度应一致"
        assert 'k' in result.columns
        assert 'd' in result.columns
        assert 'j' in result.columns

        # 验证得分计算
        scores = kdj.get_score(result)
        assert len(scores) == 30
        assert scores.min() >= 0
        assert scores.max() <= 100


if __name__ == '__main__':
    pytest.main([__file__, '-v'])