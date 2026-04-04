# -*- coding: utf-8 -*-
"""因子打分器"""

from typing import List, Dict
import pandas as pd

from factors.base import Factor


class FactorScorer:
    """因子打分器
    
    计算各因子得分并加权合成
    """
    
    def __init__(self, factors: List[Factor]):
        self.factors = factors
    
    def score(self, data: pd.DataFrame) -> pd.Series:
        """计算综合得分
        
        Args:
            data: 日K线数据
            
        Returns:
            综合得分序列
        """
        total_score = pd.Series(0.0, index=data.index)
        
        for factor in self.factors:
            factor_value = factor.calculate(data)
            # 标准化到0-100分
            normalized = self._normalize(factor_value)
            # 加权
            total_score += normalized * factor.weight
        
        return total_score
    
    def _normalize(self, values: pd.Series) -> pd.Series:
        """标准化因子值到0-100分
        
        Args:
            values: 原始因子值
            
        Returns:
            标准化后的分数
        """
        # TODO: 实现标准化逻辑
        # 可使用 min-max 或 rank 方法
        raise NotImplementedError