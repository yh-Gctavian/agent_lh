# -*- coding: utf-8 -*-
"""Data loader using AKShare"""

from typing import List
from pathlib import Path
import pandas as pd
import logging

logger = logging.getLogger('data_loader')


class DataLoader:
    """Data loader using AKShare"""
    
    def __init__(self, cache_dir: Path = None):
        self.cache_dir = cache_dir or Path('data/cache')
    
    def load_daily_data(self, symbol: str, start_date: str, end_date: str, adjust: str = 'qfq') -> pd.DataFrame:
        """Load daily K-line data"""
        try:
            import akshare as ak
            df = ak.stock_zh_a_hist(
                symbol=symbol,
                period='daily',
                start_date=start_date,
                end_date=end_date,
                adjust=adjust
            )
            df = self._standardize_columns(df)
            df['ts_code'] = f"{symbol}.SZ" if symbol.startswith(('0', '3')) else f"{symbol}.SH"
            return df
        except Exception as e:
            logger.error(f"Load failed: {symbol}, {e}")
            return pd.DataFrame()
    
    def load_stock_pool(self, pool_name: str) -> List[str]:
        """Load stock pool"""
        try:
            import akshare as ak
            if pool_name == 'hs300':
                df = ak.index_stock_cons_weight_csindex(symbol='000300')
                return df['code'].tolist()
            return []
        except Exception:
            return []
    
    def _standardize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Standardize column names"""
        mapping = {
            'date': 'trade_date', 'open': 'open', 'close': 'close',
            'high': 'high', 'low': 'low', 'volume': 'volume'
        }
        return df.rename(columns=mapping)