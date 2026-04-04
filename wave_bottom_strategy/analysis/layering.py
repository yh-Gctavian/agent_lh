# -*- coding: utf-8 -*-
"""分层分析"""

from typing import Dict, List, Optional
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
        
        # 分层
        df['layer'] = pd.qcut(df['score'], self.n_layers, labels=False, duplicates='drop')
        
        results = []
        for layer_id in sorted(df['layer'].unique()):
            layer_df = df[df['layer'] == layer_id]
            
            results.append({
                'layer': int(layer_id) + 1,
                'count': len(layer_df),
                'mean_return': layer_df['return'].mean(),
                'std_return': layer_df['return'].std(),
                'win_rate': (layer_df['return'] > 0).mean(),
                'min_score': layer_df['score'].min(),
                'max_score': layer_df['score'].max(),
            })
        
        return pd.DataFrame(results)
    
    def layer_by_factor(
        self,
        factor_values: pd.Series,
        returns: pd.Series,
        factor_name: str = ''
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
        
        if not result.empty and factor_name:
            logger.info(f"{factor_name} 分层分析完成")
        
        return result
    
    def multi_factor_layer(
        self,
        factor_dict: Dict[str, pd.Series],
        returns: pd.Series
    ) -> Dict[str, pd.DataFrame]:
        """多因子分层分析
        
        Args:
            factor_dict: {因子名: 因子值}
            returns: 后续收益率
            
        Returns:
            {因子名: 分层结果}
        """
        results = {}
        
        for factor_name, factor_values in factor_dict.items():
            layer_result = self.layer_by_factor(factor_values, returns, factor_name)
            results[factor_name] = layer_result
        
        return results
    
    def calc_ic(
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
        df = pd.DataFrame({'factor': factor_values, 'return': returns})
        df = df.dropna()
        
        if len(df) < 10:
            return 0.0
        
        # 使用秩相关系数
        ic = df['factor'].rank().corr(df['return'].rank())
        
        return ic
    
    def calc_ir(
        self,
        ic_series: pd.Series
    ) -> float:
        """计算IR（信息比率）
        
        Args:
            ic_series: IC序列
            
        Returns:
            IR值
        """
        if len(ic_series) == 0 or ic_series.std() == 0:
            return 0.0
        
        return ic_series.mean() / ic_series.std() * np.sqrt(252)
    
    def layer_returns_chart_data(
        self,
        layer_result: pd.DataFrame
    ) -> Dict:
        """生成分层收益图表数据
        
        Args:
            layer_result: 分层结果
            
        Returns:
            图表数据
        """
        if layer_result.empty:
            return {}
        
        return {
            'labels': [f"第{int(r['layer'])}层" for _, r in layer_result.iterrows()],
            'mean_returns': layer_result['mean_return'].tolist(),
            'win_rates': layer_result['win_rate'].tolist(),
            'counts': layer_result['count'].tolist(),
        }