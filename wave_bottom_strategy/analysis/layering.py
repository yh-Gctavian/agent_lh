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
        returns: pd.Series,
        layer_names: List[str] = None
    ) -> pd.DataFrame:
        """按得分分层
        
        Args:
            scores: 因子得分
            returns: 后续收益率
            layer_names: 层名称
            
        Returns:
            各层收益率统计
        """
        if layer_names is None:
            layer_names = [f'Layer{i+1}' for i in range(self.n_layers)]
        
        # 对齐索引
        common_idx = scores.index.intersection(returns.index)
        scores = scores.loc[common_idx]
        returns = returns.loc[common_idx]
        
        # 分层（按得分从低到高）
        try:
            layers = pd.qcut(scores, self.n_layers, labels=layer_names, duplicates='drop')
        except Exception as e:
            logger.warning(f"分层失败: {e}")
            return pd.DataFrame()
        
        # 计算各层统计
        results = []
        for layer_name in layers.categories:
            layer_mask = layers == layer_name
            layer_returns = returns[layer_mask]
            
            results.append({
                'layer': layer_name,
                'count': len(layer_returns),
                'mean_return': layer_returns.mean(),
                'median_return': layer_returns.median(),
                'std_return': layer_returns.std(),
                'positive_ratio': (layer_returns > 0).mean(),
                'max_return': layer_returns.max(),
                'min_return': layer_returns.min()
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
            各层统计
        """
        result = self.layer_by_score(factor_values, returns)
        
        if not result.empty:
            result['factor'] = factor_name
        
        return result
    
    def multi_factor_layering(
        self,
        factor_scores: Dict[str, pd.Series],
        returns: pd.Series
    ) -> Dict[str, pd.DataFrame]:
        """多因子分层分析
        
        Args:
            factor_scores: {因子名: 得分序列}
            returns: 收益率序列
            
        Returns:
            {因子名: 分层结果}
        """
        results = {}
        
        for factor_name, scores in factor_scores.items():
            layer_result = self.layer_by_factor(scores, returns, factor_name)
            results[factor_name] = layer_result
        
        return results
    
    def calculate_ic(
        self,
        factor_values: pd.Series,
        returns: pd.Series
    ) -> float:
        """计算IC值（Information Coefficient）
        
        Args:
            factor_values: 因子值
            returns: 收益率
            
        Returns:
            IC值（秩相关系数）
        """
        common_idx = factor_values.index.intersection(returns.index)
        
        if len(common_idx) == 0:
            return 0.0
        
        factor = factor_values.loc[common_idx]
        ret = returns.loc[common_idx]
        
        # 使用秩相关系数
        ic = factor.rank().corr(ret.rank())
        
        return ic
    
    def calculate_ir(
        self,
        factor_values: pd.Series,
        returns: pd.Series
    ) -> float:
        """计算IR值（Information Ratio）
        
        Args:
            factor_values: 因子值
            returns: 收益率
            
        Returns:
            IR值
        """
        ic = self.calculate_ic(factor_values, returns)
        
        # IR = IC均值 / IC标准差（简化版）
        # 这里直接返回IC，实际应计算多期IC的均值/标准差
        return ic
    
    def monotonicity_test(
        self,
        layer_result: pd.DataFrame
    ) -> Dict:
        """单调性检验
        
        Args:
            layer_result: 分层结果
            
        Returns:
            单调性指标
        """
        if layer_result.empty or 'mean_return' not in layer_result.columns:
            return {'monotonic': False, 'trend': 'unknown'}
        
        returns = layer_result['mean_return'].values
        
        # 检查单调性
        increasing = all(returns[i] <= returns[i+1] for i in range(len(returns)-1))
        decreasing = all(returns[i] >= returns[i+1] for i in range(len(returns)-1))
        
        # 计算趋势
        x = np.arange(len(returns))
        slope = np.polyfit(x, returns, 1)[0]
        
        return {
            'monotonic': increasing or decreasing,
            'trend': 'increasing' if slope > 0 else 'decreasing',
            'slope': slope,
            'spread': returns[-1] - returns[0] if len(returns) > 1 else 0
        }
    
    def generate_layering_report(
        self,
        factor_scores: Dict[str, pd.Series],
        returns: pd.Series
    ) -> str:
        """生成分层分析报告
        
        Args:
            factor_scores: 各因子得分
            returns: 收益率
            
        Returns:
            文本报告
        """
        lines = ["========== 分层分析报告 =========="]
        
        for factor_name, scores in factor_scores.items():
            layer_result = self.layer_by_factor(scores, returns, factor_name)
            
            if layer_result.empty:
                continue
            
            ic = self.calculate_ic(scores, returns)
            mono = self.monotonicity_test(layer_result)
            
            lines.append(f"\n--- {factor_name} ---")
            lines.append(f"IC值: {ic:.4f}")
            lines.append(f"单调性: {'✓' if mono['monotonic'] else '✗'} ({mono['trend']})")
            lines.append(f"Layer Spread: {mono['spread']:.4f}")
            
            # 各层收益
            for _, row in layer_result.iterrows():
                lines.append(
                    f"  {row['layer']}: 均值={row['mean_return']:.4f}, "
                    f"胜率={row['positive_ratio']:.2%}"
                )
        
        lines.append("\n==================================")
        
        return "\n".join(lines)