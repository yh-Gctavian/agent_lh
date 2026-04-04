# -*- coding: utf-8 -*-
"""分层分析"""

from typing import Dict, List
import pandas as pd


class LayeringAnalysis:
    """分层分析
    
    按因子分值分组，分析各组的表现差异
    """
    
    def __init__(self, n_layers: int = 5):
        self.n_layers = n_layers
    
    def layer_by_score(
        self,
        scores: pd.Series,
        returns: pd.Series
    ) -> pd.DataFrame:
        """按得分分层
        
        Args:
            scores: 因子得分
            returns: 后续收益率
            
        Returns:
            各层收益率统计
        """
        # 将得分分为n_layers层
        layers = pd.qcut(scores, self.n_layers, labels=False, duplicates='drop')
        
        results = []
        for layer_id in range(self.n_layers):
            layer_mask = layers == layer_id
            layer_returns = returns[layer_mask]
            
            results.append({
                'layer': layer_id + 1,
                'count': len(layer_returns),
                'mean_return': layer_returns.mean(),
                'std_return': layer_returns.std(),
            })
        
        return pd.DataFrame(results)
    
    def layer_by_factor(
        self,
        factor_values: pd.Series,
        returns: pd.Series,
        factor_name: str
    ) -> pd.DataFrame:
        """按单个因子值分层
        
        Args:
            factor_values: 因子值
            returns: 后续收益率
            factor_name: 因子名称
            
        Returns:
            各层收益率统计
        """
        return self.layer_by_score(factor_values, returns)