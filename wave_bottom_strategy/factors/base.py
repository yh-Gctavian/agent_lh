# -*- coding: utf-8 -*-
"""因子基类"""

from abc import ABC, abstractmethod
from typing import Dict, Any
import pandas as pd


class Factor(ABC):
    """因子基类"""
    
    def __init__(self, params: Dict[str, Any] = None):
        """初始化因子
        
        Args:
            params: 因子参数
        """
        self.params = params or {}
        self.name = self.__class__.__name__
    
    @abstractmethod
    def calculate(self, data: pd.DataFrame) -> pd.Series:
        """计算因子值
        
        Args:
            data: 日K线数据，包含 open, high, low, close, volume 等列
            
        Returns:
            因子值序列
        """
        pass
    
    @property
    @abstractmethod
    def weight(self) -> float:
        """因子权重
        
        Returns:
            权重值 (0-1)
        """
        pass
    
    def validate_data(self, data: pd.DataFrame) -> bool:
        """验证输入数据是否包含必要列
        
        Args:
            data: 日K线数据
            
        Returns:
            是否有效
        """
        required_cols = ['open', 'high', 'low', 'close', 'volume']
        return all(col in data.columns for col in required_cols)