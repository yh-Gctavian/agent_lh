# -*- coding: utf-8 -*-
"""数据预处理器"""

from typing import Optional
import pandas as pd


class DataProcessor:
    """数据预处理器"""
    
    def adjust_prices(
        self,
        df: pd.DataFrame,
        adj_factor: pd.DataFrame
    ) -> pd.DataFrame:
        """后复权处理
        
        Args:
            df: 原始日K线数据
            adj_factor: 复权因子
            
        Returns:
            复权后的数据
        """
        # TODO: 实现复权逻辑
        raise NotImplementedError
    
    def mark_suspended(
        self,
        df: pd.DataFrame,
        suspend_info: pd.DataFrame
    ) -> pd.DataFrame:
        """标记停牌日
        
        Args:
            df: 日K线数据
            suspend_info: 停牌信息
            
        Returns:
            标记停牌后的数据
        """
        # TODO: 实现停牌标记逻辑
        raise NotImplementedError
    
    def mark_delisted(
        self,
        df: pd.DataFrame,
        delist_info: pd.DataFrame
    ) -> pd.DataFrame:
        """标记退市股票
        
        Args:
            df: 日K线数据
            delist_info: 退市信息
            
        Returns:
            标记退市后的数据
        """
        # TODO: 实现退市标记逻辑
        raise NotImplementedError