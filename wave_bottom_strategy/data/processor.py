# -*- coding: utf-8 -*-
"""Data processor module"""

from typing import Optional, List, Set
import pandas as pd
from pathlib import Path
import logging

logger = logging.getLogger('data_processor')


class DataProcessor:
    """Data preprocessor for handling adjustment, suspension, delisting, ST marking"""
    
    ST_KEYWORDS = ['ST', '*ST', 'SST', 'S*ST']
    
    def __init__(self):
        self.st_stocks: Set[str] = set()
        self.delisted_stocks: Set[str] = set()
    
    def load_st_stocks(self) -> Set[str]:
        """Load ST stock list"""
        try:
            import akshare as ak
            df = ak.stock_zh_a_st_em()
            self.st_stocks = set(df['代码'].tolist())
            logger.info(f"Loaded ST stocks: {len(self.st_stocks)}")
            return self.st_stocks
        except Exception as e:
            logger.warning(f"Failed to load ST stocks: {e}")
            return set()
    
    def is_st_stock(self, symbol: str, name: str = None) -> bool:
        """Check if stock is ST"""
        if symbol in self.st_stocks:
            return True
        if name:
            for keyword in self.ST_KEYWORDS:
                if keyword in name:
                    return True
        return False
    
    def filter_stocks(
        self,
        symbols: List[str],
        exclude_st: bool = True,
        exclude_delisted: bool = True
    ) -> List[str]:
        """Filter stock pool"""
        result = symbols.copy()
        
        if exclude_st:
            self.load_st_stocks()
            result = [s for s in result if s not in self.st_stocks]
            logger.info(f"After ST filter: {len(result)}")
        
        return result
    
    def validate_data(self, df: pd.DataFrame, symbol: str) -> pd.DataFrame:
        """Validate data integrity"""
        if df.empty:
            return df
        
        df = df.dropna(subset=['open', 'high', 'low', 'close', 'volume'])
        df = df[df['high'] >= df['low']]
        df = df[df['volume'] >= 0]
        
        return df
    
    def process_all(self, df: pd.DataFrame, symbol: str, name: str = None) -> pd.DataFrame:
        """Execute all preprocessing"""
        df = self.validate_data(df, symbol)
        return df