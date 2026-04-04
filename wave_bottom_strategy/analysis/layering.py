# -*- coding: utf-8 -*-
"""分层分析"""

from typing import Dict, List
import pandas as pd
import numpy as np

from utils.logger import get_logger

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
        # 合并数据
        df = pd.DataFrame({'score': scores, 'return': returns})
        df = df.dropna()
        
        if len(df) == 0:
            return pd.DataFrame()
        
        # 分层（按得分分位数）
        df['layer'] = pd.qcut(df['score'], self.n_layers, labels=False, duplicates='drop')
        
        # 统计各层
        results = []
        for layer_id in range(self.n_layers):
            layer_data = df[df['layer'] == layer_id]
            
            if len(layer_data) == 0:
                continue
            
            results.append({
                'layer': layer_id + 1,
                'count': len(layer_data),
                'mean_return': layer_data['return'].mean(),
                'std_return': layer_data['return'].std(),
                'win_rate': (layer_data['return'] > 0).mean(),
                'mean_score': layer_data['score'].mean()
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
        factor_data: Dict[str, pd.Series],
        returns: pd.Series
    ) -> pd.DataFrame:
        """多因子分层分析
        
        Args:
            factor_data: {因子名: 因子值}
            returns: 收益率
            
        Returns:
            各因子分层结果
        """
        all_results = []
        
        for factor_name, factor_values in factor_data.items():
            result = self.layer_by_factor(factor_values, returns, factor_name)
            all_results.append(result)
        
        return pd.concat(all_results, ignore_index=True)
    
    def calc_ic(
        self,
        factor_values: pd.Series,
        returns: pd.Series
    ) -> float:
        """计算IC值（信息系数）
        
        Args:
            factor_values: 因子值
            returns: 收益率
            
        Returns:
            IC值（秩相关系数）
        """
        df = pd.DataFrame({'factor': factor_values, 'return': returns})
        df = df.dropna()
        
        if len(df) < 2:
            return 0.0
        
        # Spearman秩相关
        return df['factor'].corr(df['return'], method='spearman')
    
    def layer_returns_chart_data(
        self,
        layer_result: pd.DataFrame
    ) -> Dict:
        """生成分层收益图数据
        
        Args:
            layer_result: 分层结果
            
        Returns:
            图表数据
        """
        return {
            'x': layer_result['layer'].tolist(),
            'mean_return': layer_result['mean_return'].tolist(),
            'win_rate': layer_result['win_rate'].tolist()
        }