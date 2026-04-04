# -*- coding: utf-8 -*-
"""分层分析"""

from typing import Dict, List
import pandas as pd
import numpy as np

from wave_bottom_strategy.utils.logger import get_logger

logger = get_logger('layering_analysis')


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
        try:
            layers = pd.qcut(scores, self.n_layers, labels=False, duplicates='drop')
        except ValueError:
            # 数据不足时返回空
            return pd.DataFrame()
        
        results = []
        unique_layers = layers.unique()
        
        for layer_id in sorted(unique_layers):
            layer_mask = layers == layer_id
            layer_returns = returns[layer_mask]
            
            if len(layer_returns) > 0:
                results.append({
                    'layer': int(layer_id) + 1,
                    'count': len(layer_returns),
                    'mean_return': layer_returns.mean(),
                    'std_return': layer_returns.std(),
                    'median_return': layer_returns.median(),
                    'min_return': layer_returns.min(),
                    'max_return': layer_returns.max(),
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
        result = self.layer_by_score(factor_values, returns)
        result['factor'] = factor_name
        return result
    
    def multi_factor_layering(
        self,
        factor_data: pd.DataFrame,
        returns: pd.Series,
        factor_names: List[str]
    ) -> pd.DataFrame:
        """多因子分层分析
        
        Args:
            factor_data: 多因子数据
            returns: 收益率
            factor_names: 因子名称列表
            
        Returns:
            各因子分层结果
        """
        results = []
        
        for factor_name in factor_names:
            if factor_name in factor_data.columns:
                factor_values = factor_data[factor_name]
                layer_result = self.layer_by_factor(factor_values, returns, factor_name)
                results.append(layer_result)
        
        if results:
            return pd.concat(results, ignore_index=True)
        return pd.DataFrame()
    
    def calculate_ic(
        self,
        factor_values: pd.Series,
        returns: pd.Series
    ) -> float:
        """计算IC（信息系数）
        
        Args:
            factor_values: 因子值
            returns: 收益率
            
        Returns:
            IC值（秩相关系数）
        """
        # 使用Spearman秩相关
        return factor_values.corr(returns, method='spearman')
    
    def calculate_ir(
        self,
        ic_series: pd.Series
    ) -> float:
        """计算IR（信息比率）
        
        Args:
            ic_series: IC时间序列
            
        Returns:
            IR值（IC均值/IC标准差）
        """
        if ic_series.std() == 0:
            return 0.0
        return ic_series.mean() / ic_series.std()
    
    def layer_return_spread(
        self,
        layer_result: pd.DataFrame
    ) -> float:
        """计算层间收益差
        
        Args:
            layer_result: 分层结果
            
        Returns:
            最高层与最低层收益差
        """
        if layer_result.empty:
            return 0.0
        
        top_return = layer_result['mean_return'].max()
        bottom_return = layer_result['mean_return'].min()
        
        return top_return - bottom_return