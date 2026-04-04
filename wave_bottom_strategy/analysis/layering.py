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
    用于验证因子有效性
    """
    
    def __init__(self, n_layers: int = 5):
        self.n_layers = n_layers
    
    def layer_by_score(
        self,
        scores: pd.Series,
        forward_returns: pd.Series
    ) -> pd.DataFrame:
        """按得分分层分析
        
        Args:
            scores: 因子得分（越大越好）
            forward_returns: 未来收益率
            
        Returns:
            各层收益率统计
        """
        # 合并数据
        df = pd.DataFrame({
            'score': scores,
            'return': forward_returns
        }).dropna()
        
        if df.empty:
            return pd.DataFrame()
        
        # 分层（得分越高层数越大）
        df['layer'] = pd.qcut(df['score'], self.n_layers, labels=False, duplicates='drop')
        
        # 统计各层
        results = []
        for layer_id in sorted(df['layer'].unique()):
            layer_df = df[df['layer'] == layer_id]
            
            results.append({
                'layer': layer_id + 1,
                'count': len(layer_df),
                'mean_return': layer_df['return'].mean(),
                'median_return': layer_df['return'].median(),
                'std_return': layer_df['return'].std(),
                'win_rate': (layer_df['return'] > 0).mean(),
                'max_return': layer_df['return'].max(),
                'min_return': layer_df['return'].min()
            })
        
        return pd.DataFrame(results)
    
    def layer_by_factor(
        self,
        factor_values: pd.Series,
        forward_returns: pd.Series,
        factor_name: str = ''
    ) -> pd.DataFrame:
        """按单个因子值分层
        
        Args:
            factor_values: 因子值
            forward_returns: 未来收益率
            factor_name: 因子名称
            
        Returns:
            分层结果
        """
        result = self.layer_by_score(factor_values, forward_returns)
        
        if not result.empty:
            result['factor'] = factor_name
        
        return result
    
    def multi_factor_layering(
        self,
        factor_data: Dict[str, pd.Series],
        forward_returns: pd.Series
    ) -> pd.DataFrame:
        """多因子分层分析
        
        Args:
            factor_data: {因子名: 因子值}
            forward_returns: 未来收益率
            
        Returns:
            各因子分层结果汇总
        """
        all_results = []
        
        for factor_name, factor_values in factor_data.items():
            layer_result = self.layer_by_factor(factor_values, forward_returns, factor_name)
            all_results.append(layer_result)
        
        if all_results:
            return pd.concat(all_results, ignore_index=True)
        
        return pd.DataFrame()
    
    def calculate_ic(
        self,
        factor_values: pd.Series,
        forward_returns: pd.Series
    ) -> Dict:
        """计算IC值（信息系数）
        
        Args:
            factor_values: 因子值
            forward_returns: 未来收益率
            
        Returns:
            IC统计
        """
        df = pd.DataFrame({
            'factor': factor_values,
            'return': forward_returns
        }).dropna()
        
        if df.empty:
            return {}
        
        # 相关系数
        ic = df['factor'].corr(df['return'])
        
        # Rank IC
        rank_ic = df['factor'].rank().corr(df['return'].rank())
        
        return {
            'IC': ic,
            'Rank_IC': rank_ic,
            'IC_mean': ic,  # 单期
            'ICIR': ic  # 单期简化
        }
    
    def get_layer_spread(self, layer_result: pd.DataFrame) -> float:
        """计算层间收益差
        
        Args:
            layer_result: 分层结果
            
        Returns:
            最高层-最低层收益差
        """
        if layer_result.empty:
            return 0.0
        
        max_layer = layer_result['mean_return'].max()
        min_layer = layer_result['mean_return'].min()
        
        return max_layer - min_layer
    
    def plot_layer_returns(self, layer_result: pd.DataFrame):
        """绘制分层收益图
        
        Args:
            layer_result: 分层结果
        """
        try:
            import matplotlib.pyplot as plt
            
            fig, ax = plt.subplots(figsize=(10, 6))
            
            x = layer_result['layer']
            y = layer_result['mean_return'] * 100
            
            ax.bar(x, y, color='steelblue')
            ax.axhline(y=0, color='red', linestyle='--', linewidth=0.5)
            
            ax.set_xlabel('Layer')
            ax.set_ylabel('Mean Return (%)')
            ax.set_title('Layer Analysis')
            
            plt.tight_layout()
            plt.savefig('layer_analysis.png')
            plt.close()
            
            logger.info("分层图已保存: layer_analysis.png")
            
        except Exception as e:
            logger.warning(f"绘图失败: {e}")