# -*- coding: utf-8 -*-
"""基准对比"""

from typing import Dict
import pandas as pd


class Benchmark:
    """基准对比（沪深300等）"""
    
    def __init__(self, benchmark_code: str = "000300.SH"):
        self.benchmark_code = benchmark_code
        self.data: pd.DataFrame = None
    
    def load_data(self, start_date: str, end_date: str):
        """加载基准数据
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
        """
        # TODO: 实现基准数据加载
        raise NotImplementedError
    
    def get_returns(self) -> pd.Series:
        """获取基准收益率序列
        
        Returns:
            日收益率序列
        """
        # TODO: 实现收益率计算
        raise NotImplementedError
    
    def compare(self, strategy_returns: pd.Series) -> Dict:
        """对比策略与基准表现
        
        Args:
            strategy_returns: 策略日收益率
            
        Returns:
            对比结果
        """
        # TODO: 实现对比逻辑
        raise NotImplementedError