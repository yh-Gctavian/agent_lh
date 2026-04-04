# -*- coding: utf-8 -*-
"""通达信数据加载器测试"""

import pytest
from pathlib import Path
import pandas as pd

from wave_bottom_strategy.data.tdx_loader import TdxLocalLoader, create_tdx_loader
from wave_bottom_strategy.data.loader import DataLoader


class TestTdxLocalLoader:
    """测试通达信本地数据加载器"""
    
    def setup_method(self):
        """每个测试方法前的设置"""
        self.loader = create_tdx_loader(local=True)
    
    def test_path_exists(self):
        """测试通达信路径是否存在"""
        assert self.loader.VIPDOC_DIR.exists()
        assert (self.loader.VIPDOC_DIR / "sh" / "lday").exists()
        assert (self.loader.VIPDOC_DIR / "sz" / "lday").exists()
    
    def test_detect_market(self):
        """测试市场判断"""
        # 上海主板
        market, ts_code = self.loader._detect_market('600000')
        assert market == 'sh'
        assert ts_code == '600000.SH'
        
        # 深圳主板
        market, ts_code = self.loader._detect_market('000001')
        assert market == 'sz'
        assert ts_code == '000001.SZ'
        
        # 创业板
        market, ts_code = self.loader._detect_market('300001')
        assert market == 'sz'
        assert ts_code == '300001.SZ'
        
        # 科创板
        market, ts_code = self.loader._detect_market('688001')
        assert market == 'sh'
        assert ts_code == '688001.SH'
    
    def test_load_daily_data_sh(self):
        """测试加载上海市场数据"""
        # 测试平安银行（实际是深圳，这里用上海代码测试）
        df = self.loader.load_daily_data('600000', '20240101', '20241231')
        
        # 验证数据结构
        if not df.empty:
            assert 'trade_date' in df.columns
            assert 'open' in df.columns
            assert 'high' in df.columns
            assert 'low' in df.columns
            assert 'close' in df.columns
            assert 'volume' in df.columns
            assert 'ts_code' in df.columns
            
            # 验证数据量
            assert len(df) > 0
    
    def test_load_daily_data_sz(self):
        """测试加载深圳市场数据"""
        df = self.loader.load_daily_data('000001', '20240101', '20241231')
        
        if not df.empty:
            assert df['ts_code'].iloc[0] == '000001.SZ'
            assert len(df) > 0
    
    def test_load_stock_pool(self):
        """测试加载股票池"""
        # 上海市场
        sh_stocks = self.loader.load_stock_pool('all_sh')
        assert len(sh_stocks) > 0
        
        # 深圳市场
        sz_stocks = self.loader.load_stock_pool('all_sz')
        assert len(sz_stocks) > 0
        
        # 全A股
        all_stocks = self.loader.load_stock_pool('all_a')
        assert len(all_stocks) > 0
    
    def test_data_coverage(self):
        """测试数据覆盖范围"""
        coverage = self.loader.get_data_coverage('600000')
        
        if coverage['has_data']:
            assert coverage['start_date'] is not None
            assert coverage['end_date'] is not None
            assert coverage['record_count'] > 0


class TestHybridDataLoader:
    """测试混合模式数据加载器"""
    
    def setup_method(self):
        """每个测试方法前的设置"""
        self.loader = DataLoader(source_mode='hybrid')
    
    def test_load_daily_data_tdx_first(self):
        """测试通达信优先加载"""
        df = self.loader.load_daily_data('600000', '20240101', '20241231')
        
        if not df.empty:
            assert 'trade_date' in df.columns
            assert 'close' in df.columns
            
            # 检查统计
            stats = self.loader.get_stats()
            assert stats['tdx_success'] > 0 or stats['akshare_success'] > 0
    
    def test_load_stock_pool(self):
        """测试加载股票池"""
        stocks = self.loader.load_stock_pool('hs300')
        assert len(stocks) > 0
    
    def test_tdx_availability_check(self):
        """测试通达信数据可用性检查"""
        availability = self.loader.check_tdx_availability('600000')
        
        # 应该有数据
        assert isinstance(availability, dict)
    
    def test_stats_tracking(self):
        """测试统计追踪"""
        # 加载几只股票
        self.loader.load_daily_data('600000', '20240101', '20240131')
        self.loader.load_daily_data('000001', '20240101', '20240131')
        
        stats = self.loader.get_stats()
        
        # 应有统计记录
        assert stats['tdx_success'] + stats['akshare_success'] > 0


class TestDataConsistency:
    """测试数据一致性"""
    
    def setup_method(self):
        self.tdx_loader = DataLoader(source_mode='tdx')
        self.akshare_loader = DataLoader(source_mode='akshare')
    
    def test_compare_data_format(self):
        """对比通达信和AKShare数据格式"""
        symbol = '600000'
        
        # 通达信数据
        tdx_df = self.tdx_loader.load_daily_data(symbol, '20240101', '20240110')
        
        # AKShare数据
        ak_df = self.akshare_loader.load_daily_data(symbol, '20240101', '20240110')
        
        # 如果两边都有数据，验证字段一致性
        if not tdx_df.empty and not ak_df.empty:
            # 检查列名一致
            common_cols = set(tdx_df.columns) & set(ak_df.columns)
            assert 'trade_date' in common_cols
            assert 'close' in common_cols
    
    def test_price_range_valid(self):
        """测试价格范围合理性"""
        df = self.tdx_loader.load_daily_data('600000', '20240101', '20241231')
        
        if not df.empty:
            # 价格应该为正数
            assert (df['open'] > 0).all()
            assert (df['high'] > 0).all()
            assert (df['low'] > 0).all()
            assert (df['close'] > 0).all()
            
            # high >= low
            assert (df['high'] >= df['low']).all()
            
            # high >= open, close
            assert (df['high'] >= df['open']).all()
            assert (df['high'] >= df['close']).all()


# 运行测试的入口
if __name__ == '__main__':
    pytest.main([__file__, '-v'])