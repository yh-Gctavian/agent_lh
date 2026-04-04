# -*- coding: utf-8 -*-
"""
M1 数据层测试用例

测试数据加载器功能

创建日期：2026-04-04
编写人：量化测试经理 (mZ9QZZ)
"""

import pytest
import pandas as pd
from pathlib import Path
import sys

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from wave_bottom_strategy.data.loader import DataLoader


class TestDataLoader:
    """数据加载器测试"""
    
    @pytest.fixture
    def data_loader(self):
        """创建数据加载器实例"""
        return DataLoader(cache_dir=Path('data/cache'))
    
    def test_load_daily_data(self, data_loader):
        """DL-001: 测试日K线数据加载
        
        验证能正确加载单只股票日K线数据
        """
        # 加载平安银行 2020-2023 数据
        df = data_loader.load_daily_data(
            symbol='000001',
            start_date='20200101',
            end_date='20231231',
            adjust='qfq'
        )
        
        # 验证数据不为空
        assert not df.empty, "数据加载失败，返回空DataFrame"
        
        # 验证必要列存在
        required_cols = ['trade_date', 'open', 'close', 'high', 'low', 'volume']
        for col in required_cols:
            assert col in df.columns, f"缺少必要列: {col}"
        
        # 验证数据量合理（约1200天交易日）
        assert len(df) > 1000, f"数据量异常，仅{len(df)}条记录"
        
        print(f"✓ 日K线加载成功: {len(df)}条记录")
    
    def test_load_stock_pool_hs300(self, data_loader):
        """DL-002: 测试沪深300股票池加载
        
        验证能正确加载沪深300成分股列表
        """
        stocks = data_loader.load_stock_pool('hs300')
        
        # 验证股票数量
        assert len(stocks) > 0, "股票池加载失败"
        assert len(stocks) >= 300, f"沪深300应有至少300只股票，实际{len(stocks)}"
        
        print(f"✓ 沪深300股票池加载成功: {len(stocks)}只股票")
    
    def test_load_trade_calendar(self, data_loader):
        """DL-003: 测试交易日历加载
        
        验证能正确加载交易日历
        """
        dates = data_loader.load_trade_calendar('20200101', '20231231')
        
        # 验证交易日数量（约1000天）
        assert len(dates) > 900, f"交易日数量异常，仅{len(dates)}天"
        
        print(f"✓ 交易日历加载成功: {len(dates)}天交易日")
    
    def test_data_date_range(self, data_loader):
        """DL-004: 测试数据时间范围
        
        验证数据时间范围符合预期
        """
        df = data_loader.load_daily_data(
            symbol='000001',
            start_date='20240101',
            end_date='20241231',
            adjust='qfq'
        )
        
        # 验证时间范围
        min_date = df['trade_date'].min()
        max_date = df['trade_date'].max()
        
        assert min_date.year >= 2024, f"数据起始年份应为2024，实际{min_date.year}"
        assert max_date.year <= 2024, f"数据结束年份应为2024，实际{max_date.year}"
        
        print(f"✓ 数据时间范围正确: {min_date} ~ {max_date}")
    
    def test_data_no_missing_values(self, data_loader):
        """DL-005: 测试数据无缺失值
        
        验证关键列无缺失值
        """
        df = data_loader.load_daily_data(
            symbol='000001',
            start_date='20230101',
            end_date='20231231',
            adjust='qfq'
        )
        
        # 验证关键列无缺失
        for col in ['open', 'close', 'high', 'low', 'volume']:
            missing = df[col].isnull().sum()
            assert missing == 0, f"{col}列存在{missing}个缺失值"
        
        print(f"✓ 数据无缺失值验证通过")


class TestDataProcessor:
    """数据处理器测试"""
    
    def test_processor_import(self):
        """DP-001: 测试数据处理器可导入"""
        from wave_bottom_strategy.data.processor import DataProcessor
        print("✓ DataProcessor可正常导入")
    
    def test_processor_instance(self):
        """DP-002: 测试数据处理器实例化"""
        from wave_bottom_strategy.data.processor import DataProcessor
        processor = DataProcessor()
        assert processor is not None, "DataProcessor实例化失败"
        print("✓ DataProcessor实例化成功")


class TestDataCache:
    """数据缓存测试"""
    
    def test_cache_import(self):
        """DC-001: 测试数据缓存可导入"""
        from wave_bottom_strategy.data.cache import DataCache
        print("✓ DataCache可正常导入")
    
    def test_cache_instance(self):
        """DC-002: 测试数据缓存实例化"""
        from wave_bottom_strategy.data.cache import DataCache
        cache = DataCache(cache_dir=Path('data/cache'))
        assert cache is not None, "DataCache实例化失败"
        print("✓ DataCache实例化成功")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])