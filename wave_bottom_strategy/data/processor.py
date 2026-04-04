# -*- coding: utf-8 -*-
"""数据预处理器"""

from typing import Optional, List, Set
import pandas as pd
from pathlib import Path
import logging

logger = logging.getLogger('data_processor')


class DataProcessor:
    """数据预处理器 - 处理复权、停牌、退市、ST标记等"""
    
    ST_KEYWORDS = ['ST', '*ST', 'SST', 'S*ST']
    
    def __init__(self):
        self.st_stocks: Set[str] = set()
        self.delisted_stocks: Set[str] = set()
    
    def load_st_stocks(self) -> Set[str]:
        """加载ST股票列表"""
        try:
            import akshare as ak
            df = ak.stock_zh_a_st_em()
            self.st_stocks = set(df['代码'].tolist())
            logger.info(f"加载ST股票: {len(self.st_stocks)}只")
            return self.st_stocks
        except Exception as e:
            logger.warning(f"加载ST股票失败: {e}")
            return set()
    
    def is_st_stock(self, symbol: str, name: str = None) -> bool:
        """判断是否为ST股票"""
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
        """过滤股票池"""
        result = symbols.copy()
        
        if exclude_st:
            self.load_st_stocks()
            result = [s for s in result if s not in self.st_stocks]
        
        return result
    
    def validate_data(self, df: pd.DataFrame, symbol: str) -> pd.DataFrame:
        """验证数据完整性"""
        if df.empty:
            return df
        
        df = df.dropna(subset=['open', 'high', 'low', 'close', 'volume'])
        df = df[df['high'] >= df['low']]
        df = df[df['volume'] >= 0]
        
        return df
    
    def process_all(self, df: pd.DataFrame, symbol: str, name: str = None) -> pd.DataFrame:
        """执行全部预处理"""
        df = self.validate_data(df, symbol)
        return df