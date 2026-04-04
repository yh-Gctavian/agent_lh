# -*- coding: utf-8 -*-
"""Data processor"""

from typing import List, Set
import pandas as pd
import logging

logger = logging.getLogger('data_processor')


class DataProcessor:
    """Data preprocessor"""
    
    def __init__(self):
        self.st_stocks: Set[str] = set()
    
    def filter_stocks(self, symbols: List[str], exclude_st: bool = True) -> List[str]:
        """Filter stock pool"""
        result = symbols
        if exclude_st:
            result = [s for s in result if s not in self.st_stocks]
        return result
    
    def validate_data(self, df: pd.DataFrame, symbol: str) -> pd.DataFrame:
        """Validate data"""
        if df.empty:
            return df
        df = df.dropna(subset=['open', 'high', 'low', 'close', 'volume'])
        return df