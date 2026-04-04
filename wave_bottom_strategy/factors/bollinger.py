# -*- coding: utf-8 -*-
"""布林带因子"""

from typing import Dict, Any
import pandas as pd

from .base import Factor


class BollingerFactor(Factor):
    """布林带因子
    
    参数:
        period: 周期，默认20
        std_dev: 标准差倍数，默认2.0
    """
    
    def __init__(self, params: Dict[str, Any] = None):
        super().__init__(params)
        self.period = self.params.get('period', 20)
        self.std_dev = self.params.get('std_dev', 2.0)
    
    def calculate(self, data: pd.DataFrame) -> pd.Series:
        """计算布林带因子值
        
        Args:
            data: 日K线数据
            
        Returns:
            布林带位置因子 (收盘价相对布林带的位置)
        """
        # TODO: 使用 talib.BBANDS 实现
        raise NotImplementedError
    
    @property
    def weight(self) -> float:
        return 0.05  # 5% 权重