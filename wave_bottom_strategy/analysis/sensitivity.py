# -*- coding: utf-8 -*-
"""参数敏感性分析 - 分析参数变化对策略表现的影响"""

from typing import Dict, List, Any, Callable, Optional
import pandas as pd
import numpy as np
from itertools import product

from wave_bottom_strategy.utils.logger import get_logger

logger = get_logger('sensitivity')


class SensitivityAnalysis:
    """参数敏感性分析
    
    分析各参数变化对策略表现的影响：
    - 单参数敏感性
    - 多参数组合测试
    - 参数重要性排序
    """
    
    def __init__(self, param_ranges: Dict[str, List[Any]] = None):
        """
        Args:
            param_ranges: 参数范围 {参数名: [值列表]}
        """
        self.param_ranges = param_ranges or {}
        self.results: pd.DataFrame = pd.DataFrame()
    
    def set_param_ranges(self, ranges: Dict[str, List[Any]]):
        """设置参数范围"""
        self.param_ranges = ranges
    
    def generate_combinations(self) -> List[Dict]:
        """生成参数组合"""
        if not self.param_ranges:
            return [{}]
        
        keys = list(self.param_ranges.keys())
        values = list(self.param_ranges.values())
        
        combos = [dict(zip(keys, combo)) for combo in product(*values)]
        
        logger.info(f"生成参数组合: {len(combos)}个")
        
        return combos
    
    def run_analysis(
        self,
        backtest_func: Callable,
        base_params: Dict = None,
        metric_names: List[str] = None
    ) -> pd.DataFrame:
        """运行敏感性分析
        
        Args:
            backtest_func: 回测函数（接收参数，返回指标字典）
            base_params: 基础参数
            metric_names: 需记录的指标名
            
        Returns:
            分析结果DataFrame
        """
        combinations = self.generate_combinations()
        base_params = base_params or {}
        
        results = []
        
        for i, params in enumerate(combinations):
            full_params = {**base_params, **params}
            
            try:
                logger.info(f"测试组合 {i+1}/{len(combinations)}: {params}")
                
                metrics = backtest_func(full_params)
                
                result = {**params}
                
                if metric_names:
                    for m in metric_names:
                        result[m] = metrics.get(m, None)
                else:
                    result.update(metrics)
                
                results.append(result)
                
            except Exception as e:
                logger.warning(f"测试失败: {params}, {e}")
                results.append({**params, 'error': str(e)})
        
        self.results = pd.DataFrame(results)
        
        logger.info(f"敏感性分析完成: {len(self.results)}条结果")
        
        return self.results
    
    def analyze_single_param(
        self,
        param_name: str,
        param_values: List[Any],
        backtest_func: Callable,
        base_params: Dict = None,
        metric: str = 'sharpe_ratio'
    ) -> pd.DataFrame:
        """单参数敏感性分析
        
        固定其他参数，只变化一个参数
        
        Args:
            param_name: 参数名
            param_values: 参数值列表
            backtest_func: 回测函数
            base_params: 其他参数固定值
            metric: 目标指标
            
        Returns:
            单参数分析结果
        """
        base_params = base_params or {}
        
        results = []
        
        for value in param_values:
            params = {**base_params, param_name: value}
            
            try:
                metrics = backtest_func(params)
                
                results.append({
                    param_name: value,
                    metric: metrics.get(metric, None)
                })
                
            except Exception as e:
                results.append({param_name: value, metric: None, 'error': str(e)})
        
        df = pd.DataFrame(results)
        
        return df
    
    def find_optimal(
        self,
        results: pd.DataFrame = None,
        metric: str = 'sharpe_ratio',
        top_n: int = 5
    ) -> List[Dict]:
        """找出最优参数
        
        Args:
            results: 分析结果
            metric: 目标指标
            top_n: 返回前N个
            
        Returns:
            最优参数列表
        """
        df = results or self.results
        
        if df.empty or metric not in df.columns:
            return []
        
        valid = df[df[metric].notna() & (df.get('error', pd.Series()).isna() if 'error' in df.columns else True)]
        
        if valid.empty:
            return []
        
        top = valid.nlargest(top_n, metric)
        
        return top.to_dict('records')
    
    def calc_param_importance(
        self,
        results: pd.DataFrame = None,
        metric: str = 'sharpe_ratio'
    ) -> pd.DataFrame:
        """计算参数重要性
        
        分析各参数对指标变化的贡献度
        
        Args:
            results: 分析结果
            metric: 目标指标
            
        Returns:
            参数重要性排序
        """
        df = results or self.results
        
        if df.empty or metric not in df.columns:
            return pd.DataFrame()
        
        importance = []
        
        for param_name in self.param_ranges.keys():
            if param_name not in df.columns:
                continue
            
            # 按参数值分组，计算指标变化幅度
            grouped = df.groupby(param_name)[metric].agg(['mean', 'std'])
            
            if len(grouped) > 1:
                # 指标变化范围
                range_val = grouped['mean'].max() - grouped['mean'].min()
                std_val = grouped['std'].mean()
                
                importance.append({
                    'param': param_name,
                    'impact_range': range_val,
                    'impact_std': std_val,
                    'n_values': len(grouped)
                })
        
        importance_df = pd.DataFrame(importance)
        
        if not importance_df.empty:
            importance_df['importance_rank'] = importance_df['impact_range'].rank(ascending=False)
        
        return importance_df.sort_values('importance_rank')
    
    def generate_heatmap_data(
        self,
        param_x: str,
        param_y: str,
        metric: str = 'sharpe_ratio'
    ) -> pd.DataFrame:
        """生成热力图数据
        
        用于可视化两个参数组合的效果
        
        Args:
            param_x: X轴参数
            param_y: Y轴参数
            metric: 目标指标
            
        Returns:
            热力图矩阵
        """
        if self.results.empty:
            return pd.DataFrame()
        
        pivot = self.results.pivot_table(
            values=metric,
            index=param_y,
            columns=param_x,
            aggfunc='mean'
        )
        
        return pivot
    
    def generate_report(self) -> Dict:
        """生成敏感性分析报告"""
        if self.results.empty:
            return {}
        
        report = {
            'total_combinations': len(self.results),
            'param_count': len(self.param_ranges),
            'best_params': self.find_optimal(),
            'param_importance': self.calc_param_importance().to_dict('records')
        }
        
        return report