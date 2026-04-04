# -*- coding: utf-8 -*-
"""RSI因子"""

from typing import Dict, Any
import pandas as pd

from .base import Factor


class RSIFactor(Factor):
    """RSI相对强弱指标因子
    
    参数:
        period: RSI周期，默认14
    """
    
    def __init__(self, params: Dict[str, Any] = None):
        super().__init__(params)
        self.period = self.params.get('period', 14)
    
    def calculate(self, data: pd.DataFrame) -> pd.Series:
        """计算RSI值
        
        Args:
            data: 日K线数据
            
        Returns:
            RSI值序列
        """
        # TODO: 使用 talib.RSI 实现
        raise NotImplementedError
    
    @property
    def weight(self) -> float:
        return 0.10  # 10% 权重