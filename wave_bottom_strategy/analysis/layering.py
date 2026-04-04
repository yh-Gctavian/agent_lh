# -*- coding: utf-8 -*-
"""分层分析"""

from typing import Dict, List
import pandas as pd
import numpy as np

from utils.logger import get_logger

logger = get_logger('layering_analysis')


class LayeringAnalysis:
    """分层分析
    
    按因子分值分组，分析各组表现差异
    """
    
    def __init__(self, n_layers: int = 5):
        self.n_layers = n_layers
    
    def layer_by_score(
        self,
        scores: pd.Series,
        returns: pd.Series
    ) -> pd.DataFrame:
        """按得分分层"""
        # 合并数据
        df = pd.DataFrame({'score': scores, 'return': returns})
        df = df.dropna()
        
        if df.empty:
            return pd.DataFrame()
        
        # 分层
        df['layer'] = pd.qcut(df['score'], self.n_layers, labels=False, duplicates='drop')
        
        # 统计各层
        results = []
        for layer_id in range(self.n_layers):
            layer_df = df[df['layer'] == layer_id]
            
            if layer_df.empty:
                continue
            
            results.append({
                'layer': layer_id + 1,
                'count': len(layer_df),
                'mean_return': layer_df['return'].mean(),
                'std_return': layer_df['return'].std(),
                'win_rate': (layer_df['return'] > 0).mean(),
                'min_score': layer_df['score'].min(),
                'max_score': layer_df['score'].max()
            })
        
        return pd.DataFrame(results)
    
    def layer_by_factor(
        self,
        factor_values: pd.DataFrame,
        returns: pd.Series,
        factor_name: str
    ) -> pd.DataFrame:
        """按单因子分层"""
        if factor_name not in factor_values.columns:
            logger.warning(f"因子 {factor_name} 不存在")
            return pd.DataFrame()
        
        return self.layer_by_score(factor_values[factor_name], returns)
    
    def calc_ic(
        self,
        factor_values: pd.Series,
        returns: pd.Series
    ) -> float:
        """计算IC值"""
        df = pd.DataFrame({'factor': factor_values, 'return': returns})
        df = df.dropna()
        
        if df.empty:
            return 0.0
        
        return df['factor'].corr(df['return'])
    
    def calc_ir(
        self,
        factor_values: pd.Series,
        returns: pd.Series
    ) -> float:
        """计算IR值（IC均值/IC标准差）"""
        # 简化实现
        ic = self.calc_ic(factor_values, returns)
        return ic  # 实际应计算多期IC的均值/标准差
    
    def summary_report(
        self,
        factor_data: Dict[str, pd.Series],
        returns: pd.Series
    ) -> pd.DataFrame:
        """生成因子分层汇总报告"""
        results = []
        
        for factor_name, factor_values in factor_data.items():
            layer_result = self.layer_by_score(factor_values, returns)
            ic = self.calc_ic(factor_values, returns)
            
            if not layer_result.empty:
                results.append({
                    'factor': factor_name,
                    'ic': ic,
                    'layer1_return': layer_result[layer_result['layer'] == 1]['mean_return'].iloc[0] if len(layer_result[layer_result['layer'] == 1]) > 0 else 0,
                    'layer5_return': layer_result[layer_result['layer'] == 5]['mean_return'].iloc[0] if len(layer_result[layer_result['layer'] == 5]) > 0 else 0,
                    'spread': layer_result[layer_result['layer'] == 5]['mean_return'].iloc[0] - layer_result[layer_result['layer'] == 1]['mean_return'].iloc[0] if len(layer_result) >= 5 else 0
                })
        
        return pd.DataFrame(results)