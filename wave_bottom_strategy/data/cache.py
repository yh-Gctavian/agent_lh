# -*- coding: utf-8 -*-
"""数据缓存管理"""

from pathlib import Path
from typing import Optional, Dict, List
import pandas as pd
import os
from datetime import datetime

from wave_bottom_strategy.utils.logger import get_logger

logger = get_logger('data_cache')


class DataCache:
    """数据缓存管理
    
    使用Parquet格式存储数据，支持高效读�?
    """
    
    def __init__(self, cache_dir: Path = None):
        self.cache_dir = cache_dir or Path('data/cache')
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # 子目�?
        self.daily_dir = self.cache_dir / 'daily'
        self.factor_dir = self.cache_dir / 'factors'
        self.pool_dir = self.cache_dir / 'pools'
        
        for d in [self.daily_dir, self.factor_dir, self.pool_dir]:
            d.mkdir(exist_ok=True)
    
    def save_daily(
        self,
        df: pd.DataFrame,
        symbol: str,
        start_date: str,
        end_date: str
    ) -> Path:
        """保存日K线数�?
        
        Args:
            df: 日K线数�?
            symbol: 股票代码
            start_date: 开始日�?
            end_date: 结束日期
            
        Returns:
            缓存文件路径
        """
        filename = f"{symbol}_{start_date}_{end_date}.parquet"
        filepath = self.daily_dir / filename
        
        df.to_parquet(filepath, index=False, engine='pyarrow')
        logger.info(f"保存日K线缓�? {filepath}")
        
        return filepath
    
    def load_daily(
        self,
        symbol: str,
        start_date: str,
        end_date: str
    ) -> Optional[pd.DataFrame]:
        """加载日K线缓�?
        
        Args:
            symbol: 股票代码
            start_date: 开始日�?
            end_date: 结束日期
            
        Returns:
            缓存的数据，不存在返回None
        """
        filename = f"{symbol}_{start_date}_{end_date}.parquet"
        filepath = self.daily_dir / filename
        
        if filepath.exists():
            df = pd.read_parquet(filepath, engine='pyarrow')
            logger.info(f"加载日K线缓�? {filepath}")
            return df
        
        logger.debug(f"缓存不存�? {filepath}")
        return None
    
    def save_factor(
        self,
        df: pd.DataFrame,
        factor_name: str,
        symbol: str
    ) -> Path:
        """保存因子计算结果
        
        Args:
            df: 因子数据
            factor_name: 因子名称
            symbol: 股票代码
            
        Returns:
            缓存文件路径
        """
        factor_subdir = self.factor_dir / factor_name
        factor_subdir.mkdir(exist_ok=True)
        
        filename = f"{symbol}.parquet"
        filepath = factor_subdir / filename
        
        df.to_parquet(filepath, index=False, engine='pyarrow')
        logger.info(f"保存因子缓存: {filepath}")
        
        return filepath
    
    def load_factor(
        self,
        factor_name: str,
        symbol: str
    ) -> Optional[pd.DataFrame]:
        """加载因子缓存
        
        Args:
            factor_name: 因子名称
            symbol: 股票代码
            
        Returns:
            缓存的数据，不存在返回None
        """
        filepath = self.factor_dir / factor_name / f"{symbol}.parquet"
        
        if filepath.exists():
            return pd.read_parquet(filepath, engine='pyarrow')
        
        return None
    
    def save_stock_pool(
        self,
        symbols: List[str],
        pool_name: str
    ) -> Path:
        """保存股票�?
        
        Args:
            symbols: 股票代码列表
            pool_name: 股票池名�?
            
        Returns:
            缓存文件路径
        """
        filepath = self.pool_dir / f"{pool_name}.txt"
        
        with open(filepath, 'w') as f:
            f.write('\n'.join(symbols))
        
        logger.info(f"保存股票池缓�? {filepath}")
        return filepath
    
    def load_stock_pool(
        self,
        pool_name: str
    ) -> Optional[List[str]]:
        """加载股票池缓�?
        
        Args:
            pool_name: 股票池名�?
            
        Returns:
            股票代码列表，不存在返回None
        """
        filepath = self.pool_dir / f"{pool_name}.txt"
        
        if filepath.exists():
            with open(filepath, 'r') as f:
                symbols = [line.strip() for line in f.readlines()]
            logger.info(f"加载股票池缓�? {filepath}")
            return symbols
        
        return None
    
    def get_cache_info(self) -> Dict:
        """获取缓存信息
        
        Returns:
            缓存统计信息
        """
        info = {
            'daily_count': len(list(self.daily_dir.glob('*.parquet'))),
            'factor_count': sum(len(list(d.glob('*.parquet'))) 
                               for d in self.factor_dir.iterdir() 
                               if d.is_dir()),
            'pool_count': len(list(self.pool_dir.glob('*.txt'))),
            'total_size': self._get_dir_size(self.cache_dir)
        }
        
        return info
    
    def _get_dir_size(self, path: Path) -> int:
        """获取目录大小
        
        Args:
            path: 目录路径
            
        Returns:
            目录大小（字节）
        """
        total = 0
        for f in path.rglob('*'):
            if f.is_file():
                total += f.stat().st_size
        return total
    
    def clear_cache(self, cache_type: str = 'all'):
        """清理缓存
        
        Args:
            cache_type: 缓存类型 ('daily', 'factor', 'pool', 'all')
        """
        if cache_type == 'all':
            for d in [self.daily_dir, self.factor_dir, self.pool_dir]:
                for f in d.rglob('*'):
                    if f.is_file():
                        f.unlink()
        elif cache_type == 'daily':
            for f in self.daily_dir.glob('*.parquet'):
                f.unlink()
        elif cache_type == 'factor':
            for d in self.factor_dir.iterdir():
                if d.is_dir():
                    for f in d.glob('*.parquet'):
                        f.unlink()
        elif cache_type == 'pool':
            for f in self.pool_dir.glob('*.txt'):
                f.unlink()
        
        logger.info(f"清理缓存: {cache_type}")
    
    def is_cache_valid(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
        max_age_days: int = 7
    ) -> bool:
        """检查缓存是否有�?
        
        Args:
            symbol: 股票代码
            start_date: 开始日�?
            end_date: 结束日期
            max_age_days: 最大缓存天�?
            
        Returns:
            是否有效
        """
        filepath = self.daily_dir / f"{symbol}_{start_date}_{end_date}.parquet"
        
        if not filepath.exists():
            return False
        
        # 检查文件修改时�?
        mtime = datetime.fromtimestamp(filepath.stat().st_mtime)
        age = (datetime.now() - mtime).days
        
        return age <= max_age_days
