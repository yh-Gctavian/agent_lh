# -*- coding: utf-8 -*-
"""成交量因子"""

from typing import Dict, Any
import pandas as pd

from .base import Factor


class VolumeFactor(Factor):
    """成交量因子
    
    参数:
        ma_period: 均量周期，默认5
    """
    
    def __init__(self, params: Dict[str, Any] = None):
        super().__init__(params)
        self.ma_period = self.params.get('ma_period', 5)
    
    def calculate(self, data: pd.DataFrame) -> pd.Series:
        """计算成交量因子值
        
        Args:
            data: 日K线数据
            
        Returns:
            成交量因子值 (量比等)
        """
        # TODO: 实现成交量因子计算逻辑
        raise NotImplementedError
    
    @property
    def weight(self) -> float:
        return 0.15  # 15% 权重