# -*- coding: utf-8 -*-
"""数据缓存管理"""

from pathlib import Path
from typing import Optional, Dict, List
import pandas as pd
import logging

logger = logging.getLogger('data_cache')


class DataCache:
    """数据缓存管理 - 使用Parquet格式存储数据"""
    
    def __init__(self, cache_dir: Path = None):
        self.cache_dir = cache_dir or Path('data/cache')
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self.daily_dir = self.cache_dir / 'daily'
        self.factor_dir = self.cache_dir / 'factors'
        
        for d in [self.daily_dir, self.factor_dir]:
            d.mkdir(exist_ok=True)
    
    def save_daily(self, df: pd.DataFrame, symbol: str, start_date: str, end_date: str) -> Path:
        """保存日K线数据"""
        filename = f"{symbol}_{start_date}_{end_date}.parquet"
        filepath = self.daily_dir / filename
        df.to_parquet(filepath, index=False, engine='pyarrow')
        logger.info(f"保存日K线缓存: {filepath}")
        return filepath
    
    def load_daily(self, symbol: str, start_date: str, end_date: str) -> Optional[pd.DataFrame]:
        """加载日K线缓存"""
        filename = f"{symbol}_{start_date}_{end_date}.parquet"
        filepath = self.daily_dir / filename
        
        if filepath.exists():
            return pd.read_parquet(filepath, engine='pyarrow')
        return None
    
    def get_cache_info(self) -> Dict:
        """获取缓存信息"""
        return {
            'daily_count': len(list(self.daily_dir.glob('*.parquet'))),
            'cache_dir': str(self.cache_dir)
        }