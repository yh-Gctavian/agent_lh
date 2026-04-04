# -*- coding: utf-8 -*-
"""数据加载器"""

from typing import Optional, List
from pathlib import Path
import pandas as pd


class DataLoader:
    """数据加载器"""
    
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
    
    def load_daily_data(
        self,
        ts_code: str,
        start_date: str,
        end_date: str
    ) -> pd.DataFrame:
        """加载日K线数据
        
        Args:
            ts_code: 股票代码 (如 000001.SZ)
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
            
        Returns:
            日K线DataFrame
        """
        # TODO: 实现数据加载逻辑
        raise NotImplementedError
    
    def load_stock_pool(self, pool_name: str) -> List[str]:
        """加载股票池
        
        Args:
            pool_name: 股票池名称 (如 hs300)
            
        Returns:
            股票代码列表
        """
        # TODO: 实现股票池加载逻辑
        raise NotImplementedError