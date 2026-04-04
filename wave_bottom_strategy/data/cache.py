# -*- coding: utf-8 -*-
"""Data cache"""

from pathlib import Path
import pandas as pd
import logging

logger = logging.getLogger('data_cache')


class DataCache:
    """Data cache using Parquet"""
    
    def __init__(self, cache_dir: Path = None):
        self.cache_dir = cache_dir or Path('data/cache')
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def save(self, df: pd.DataFrame, name: str) -> Path:
        """Save data to cache"""
        path = self.cache_dir / f"{name}.parquet"
        df.to_parquet(path, index=False)
        return path
    
    def load(self, name: str) -> pd.DataFrame:
        """Load data from cache"""
        path = self.cache_dir / f"{name}.parquet"
        if path.exists():
            return pd.read_parquet(path)
        return pd.DataFrame()