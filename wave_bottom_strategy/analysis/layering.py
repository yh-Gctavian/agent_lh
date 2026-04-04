# -*- coding: utf-8 -*-
"""分层分析"""

from typing import Dict, List
import pandas as pd
import numpy as np

from ..utils.logger import get_logger

logger = get_logger('layering_analysis')


class LayeringAnalysis:
    """分层分析
    
    按因子分值分组，分析各组表现
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
            各层统计
        """
        # 分层
        labels = [f'Layer{i+1}' for i in range(self.n_layers)]
        layers = pd.qcut(scores, self.n_layers, labels=labels, duplicates='drop')
        
        results = []
        for layer in layers.unique():
            mask = layers == layer
            layer_returns = returns[mask]
            
            results.append({
                'layer': layer,
                'count': len(layer_returns),
                'mean_return': layer_returns.mean(),
                'std_return': layer_returns.std(),
                'win_rate': (layer_returns > 0).mean()
            })
        
        return pd.DataFrame(results)
    
    def layer_by_factor(
        self,
        factor_values: pd.Series,
        returns: pd.Series,
        factor_name: str
    ) -> pd.DataFrame:
        """按因子值分层"""
        return self.layer_by_score(factor_values, returns)
    
    def monotonicity_test(self, layer_result: pd.DataFrame) -> float:
        """单调性检验
        
        Returns:
            单调性系数（IC）
        """
        if layer_result.empty:
            return 0.0
        
        # Spearman相关系数
        from scipy.stats import spearmanr
        x = range(len(layer_result))
        y = layer_result['mean_return'].values
        
        corr, _ = spearmanr(x, y)
        return corr