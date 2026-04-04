# -*- coding: utf-8 -*-
"""数据缓存管理"""

from pathlib import Path
from typing import Optional
import pandas as pd


class DataCache:
    """数据缓存管理"""
    
    def __init__(self, cache_dir: Path):
        self.cache_dir = cache_dir
    
    def save(
        self,
        df: pd.DataFrame,
        name: str,
        partition: Optional[str] = None
    ) -> Path:
        """保存数据到缓存
        
        Args:
            df: 数据
            name: 缓存名称
            partition: 分区标识
            
        Returns:
            缓存文件路径
        """
        # TODO: 实现缓存保存逻辑
        raise NotImplementedError
    
    def load(
        self,
        name: str,
        partition: Optional[str] = None
    ) -> Optional[pd.DataFrame]:
        """从缓存加载数据
        
        Args:
            name: 缓存名称
            partition: 分区标识
            
        Returns:
            缓存的数据，不存在返回None
        """
        # TODO: 实现缓存加载逻辑
        raise NotImplementedError