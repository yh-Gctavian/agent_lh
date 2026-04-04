# -*- coding: utf-8 -*-
"""均线因子"""

from typing import Dict, Any, List
import pandas as pd

from .base import Factor


class MAFactor(Factor):
    """移动平均线因子
    
    参数:
        periods: 均线周期列表，默认 [5, 20, 60]
    """
    
    def __init__(self, params: Dict[str, Any] = None):
        super().__init__(params)
        self.periods = self.params.get('periods', [5, 20, 60])
    
    def calculate(self, data: pd.DataFrame) -> pd.Series:
        """计算均线因子值
        
        Args:
            data: 日K线数据
            
        Returns:
            均线因子值 (基于多均线综合评分)
        """
        # TODO: 实现均线计算和综合评分逻辑
        raise NotImplementedError
    
    @property
    def weight(self) -> float:
        return 0.15  # 15% 权重