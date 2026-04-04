# -*- coding: utf-8 -*-
"""分层分析"""

from typing import Dict
import pandas as pd
import numpy as np

from utils.logger import get_logger

logger = get_logger('layering')


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
        # 分层
        labels = [f'Layer_{i+1}' for i in range(self.n_layers)]
        layers = pd.qcut(scores, self.n_layers, labels=labels, duplicates='drop')
        
        results = []
        for layer in layers.categories:
            mask = layers == layer
            layer_returns = returns[mask]
            
            results.append({
                'layer': layer,
                'count': len(layer_returns),
                'mean_return': layer_returns.mean(),
                'std_return': layer_returns.std(),
                'median_return': layer_returns.median()
            })
        
        return pd.DataFrame(results)
    
    def layer_by_factor(
        self,
        factor_values: pd.DataFrame,
        returns: pd.Series,
        factor_name: str
    ) -> pd.DataFrame:
        """按单个因子分层
        
        Args:
            factor_values: 因子值
            returns: 收益率
            factor_name: 因子名称
            
        Returns:
            分层结果
        """
        if factor_name not in factor_values.columns:
            logger.warning(f"因子{factor_name}不存在")
            return pd.DataFrame()
        
        return self.layer_by_score(factor_values[factor_name], returns)
    
    def multi_factor_layer(
        self,
        scores: pd.DataFrame,
        returns: pd.Series,
        score_col: str = 'total_score'
    ) -> pd.DataFrame:
        """多因子分层分析
        
        Args:
            scores: 评分结果
            returns: 收益率
            score_col: 评分列名
            
        Returns:
            分层结果
        """
        if score_col not in scores.columns:
            logger.warning(f"评分列{score_col}不存在")
            return pd.DataFrame()
        
        return self.layer_by_score(scores[score_col], returns)
    
    def calc_ic(
        self,
        factor_values: pd.Series,
        returns: pd.Series
    ) -> float:
        """计算IC值
        
        Args:
            factor_values: 因子值
            returns: 收益率
            
        Returns:
            IC值（相关系数）
        """
        aligned = pd.concat([factor_values, returns], axis=1, join='inner')
        
        if len(aligned) < 2:
            return 0
        
        return aligned.iloc[:, 0].corr(aligned.iloc[:, 1])
    
    def layer_turnover(
        self,
        layers_series: pd.Series
    ) -> pd.DataFrame:
        """计算各层换手率
        
        Args:
            layers_series: 各期分层结果
            
        Returns:
            换手率统计
        """
        # 计算相邻期间分层变化
        turnover = []
        
        for i in range(1, len(layers_series)):
            prev = layers_series.iloc[i-1]
            curr = layers_series.iloc[i]
            
            changed = (prev != curr).sum()
            total = len(prev)
            
            turnover.append(changed / total if total > 0 else 0)
        
        return pd.DataFrame({'turnover': turnover})