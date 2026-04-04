# -*- coding: utf-8 -*-
"""MACD因子"""

from typing import Dict, Any
import pandas as pd

from .base import Factor


class MACDFactor(Factor):
    """MACD因子
    
    参数:
        fast: 快线周期，默认12
        slow: 慢线周期，默认26
        signal: 信号线周期，默认9
    """
    
    def __init__(self, params: Dict[str, Any] = None):
        super().__init__(params)
        self.fast = self.params.get('fast', 12)
        self.slow = self.params.get('slow', 26)
        self.signal = self.params.get('signal', 9)
    
    def calculate(self, data: pd.DataFrame) -> pd.Series:
        """计算MACD值
        
        Args:
            data: 日K线数据
            
        Returns:
            MACD柱状图值 (DIF - DEA)
        """
        # TODO: 使用 talib.MACD 实现
        raise NotImplementedError
    
    @property
    def weight(self) -> float:
        return 0.10  # 10% 权重