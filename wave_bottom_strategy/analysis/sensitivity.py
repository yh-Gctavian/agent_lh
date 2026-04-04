# -*- coding: utf-8 -*-
"""参数敏感性分析"""

from typing import Dict, List, Any, Callable
import pandas as pd
import numpy as np
from itertools import product

from utils.logger import get_logger

logger = get_logger('sensitivity_analysis')


class SensitivityAnalysis:
    """参数敏感性分析
    
    测试不同参数组合下的策略表现
    """
    
    def __init__(self, param_ranges: Dict[str, List[Any]]):
        """初始化
        
        Args:
            param_ranges: 参数范围，如 {'kdj_n': [5, 9, 14], 'min_score': [50, 60, 70]}
        """
        self.param_ranges = param_ranges
    
    def generate_combinations(self) -> List[Dict]:
        """生成参数组合
        
        Returns:
            参数组合列表
        """
        keys = list(self.param_ranges.keys())
        values = list(self.param_ranges.values())
        
        combinations = []
        for combo in product(*values):
            combinations.append(dict(zip(keys, combo)))
        
        logger.info(f"生成{len(combinations)}组参数组合")
        return combinations
    
    def run_analysis(
        self,
        backtest_func: Callable,
        base_params: Dict[str, Any] = None
    ) -> pd.DataFrame:
        """运行敏感性分析
        
        Args:
            backtest_func: 回测函数
            base_params: 基础参数
            
        Returns:
            各参数组合的回测结果
        """
        results = []
        combinations = self.generate_combinations()
        
        for i, params in enumerate(combinations):
            logger.info(f"分析进度: {i+1}/{len(combinations)} - {params}")
            
            try:
                # 合并参数
                full_params = {**(base_params or {}), **params}
                
                # 运行回测
                metrics = backtest_func(full_params)
                
                results.append({
                    **params,
                    **metrics
                })
                
            except Exception as e:
                logger.warning(f"参数组合失败: {params}, {e}")
                results.append({
                    **params,
                    'error': str(e)
                })
        
        return pd.DataFrame(results)
    
    def find_optimal_params(
        self,
        results: pd.DataFrame,
        metric: str = 'sharpe_ratio',
        maximize: bool = True
    ) -> Dict:
        """找出最优参数
        
        Args:
            results: 分析结果
            metric: 优化指标
            maximize: 是否最大化
            
        Returns:
            最优参数
        """
        if results.empty or metric not in results.columns:
            return {}
        
        # 过滤错误结果
        valid = results[~results['error'].isin([np.nan, None])].copy() if 'error' in results.columns else results
        
        if valid.empty:
            return {}
        
        if maximize:
            best_idx = valid[metric].idxmax()
        else:
            best_idx = valid[metric].idxmin()
        
        return valid.loc[best_idx].to_dict()
    
    def analyze_single_param(
        self,
        results: pd.DataFrame,
        param_name: str,
        metric: str = 'sharpe_ratio'
    ) -> pd.DataFrame:
        """分析单个参数的影响
        
        Args:
            results: 分析结果
            param_name: 参数名
            metric: 分析指标
            
        Returns:
            参数值与指标的关系
        """
        if results.empty or param_name not in results.columns:
            return pd.DataFrame()
        
        grouped = results.groupby(param_name)[metric].agg(['mean', 'std', 'min', 'max'])
        
        return grouped
    
    def get_param_importance(
        self,
        results: pd.DataFrame,
        metric: str = 'sharpe_ratio'
    ) -> pd.Series:
        """计算参数重要性
        
        Args:
            results: 分析结果
            metric: 分析指标
            
        Returns:
            参数重要性排序
        """
        importance = {}
        
        for param_name in self.param_ranges.keys():
            if param_name not in results.columns:
                continue
            
            # 计算参数变化对指标的影响程度
            grouped = results.groupby(param_name)[metric].mean()
            
            if len(grouped) > 1:
                importance[param_name] = grouped.std()
        
        return pd.Series(importance).sort_values(ascending=False)
    
    def grid_search(
        self,
        backtest_func: Callable,
        params_grid: Dict[str, List[Any]],
        metric: str = 'sharpe_ratio'
    ) -> pd.DataFrame:
        """网格搜索
        
        Args:
            backtest_func: 回测函数
            params_grid: 参数网格
            metric: 优化指标
            
        Returns:
            搜索结果
        """
        self.param_ranges = params_grid
        return self.run_analysis(backtest_func)