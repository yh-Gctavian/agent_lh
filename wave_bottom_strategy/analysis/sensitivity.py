# -*- coding: utf-8 -*-
"""参数敏感性分�?""

from typing import Dict, List, Any, Callable
import pandas as pd
import numpy as np
from itertools import product

from utils.logger import get_logger

logger = get_logger('sensitivity_analysis')


class SensitivityAnalysis:
    """参数敏感性分�?
    
    测试不同参数组合下的策略表现
    """
    
    def __init__(self, param_ranges: Dict[str, List[Any]] = None):
        """初始�?
        
        Args:
            param_ranges: 参数范围，如 {'kdj_n': [5, 9, 14], 'min_score': [50, 60, 70]}
        """
        self.param_ranges = param_ranges or {}
    
    def set_param_ranges(self, param_ranges: Dict[str, List[Any]]):
        """设置参数范围"""
        self.param_ranges = param_ranges
    
    def run_analysis(
        self,
        backtest_func: Callable,
        base_params: Dict[str, Any] = None
    ) -> pd.DataFrame:
        """运行敏感性分�?
        
        Args:
            backtest_func: 回测函数，接受参数字典，返回指标字典
            base_params: 基础参数
            
        Returns:
            各参数组合的回测结果
        """
        base_params = base_params or {}
        results = []
        
        # 生成参数组合
        param_combinations = self._generate_combinations()
        total = len(param_combinations)
        
        logger.info(f"开始敏感性分析，共{total}组参数组�?)
        
        for i, params in enumerate(param_combinations):
            if i % 10 == 0:
                logger.info(f"进度: {i+1}/{total}")
            
            # 合并参数
            full_params = {**base_params, **params}
            
            try:
                # 运行回测
                metrics = backtest_func(full_params)
                results.append({
                    **params,
                    **metrics
                })
            except Exception as e:
                logger.warning(f"参数组合{params}回测失败: {e}")
                results.append({
                    **params,
                    'error': str(e)
                })
        
        return pd.DataFrame(results)
    
    def run_single_param(
        self,
        param_name: str,
        param_values: List[Any],
        backtest_func: Callable,
        base_params: Dict[str, Any] = None
    ) -> pd.DataFrame:
        """单参数敏感性分�?
        
        Args:
            param_name: 参数�?
            param_values: 参数值列�?
            backtest_func: 回测函数
            base_params: 基础参数
            
        Returns:
            各参数值的结果
        """
        base_params = base_params or {}
        results = []
        
        for value in param_values:
            params = {**base_params, param_name: value}
            
            try:
                metrics = backtest_func(params)
                results.append({
                    param_name: value,
                    **metrics
                })
            except Exception as e:
                logger.warning(f"参数{param_name}={value}回测失败: {e}")
        
        return pd.DataFrame(results)
    
    def _generate_combinations(self) -> List[Dict]:
        """生成参数组合
        
        Returns:
            参数组合列表
        """
        if not self.param_ranges:
            return [{}]
        
        # 获取参数名和值列�?
        names = list(self.param_ranges.keys())
        value_lists = [self.param_ranges[name] for name in names]
        
        # 生成笛卡尔积
        combinations = []
        for values in product(*value_lists):
            combinations.append(dict(zip(names, values)))
        
        return combinations
    
    def find_optimal_params(
        self,
        results: pd.DataFrame,
        metric: str = 'sharpe_ratio',
        maximize: bool = True
    ) -> Dict:
        """找出最优参�?
        
        Args:
            results: 分析结果
            metric: 优化指标
            maximize: 是否最大化
            
        Returns:
            最优参数组�?
        """
        if results.empty or metric not in results.columns:
            return {}
        
        # 过滤有效结果
        valid = results[results[metric].notna()]
        
        if valid.empty:
            return {}
        
        if maximize:
            best_idx = valid[metric].idxmax()
        else:
            best_idx = valid[metric].idxmin()
        
        return valid.loc[best_idx].to_dict()
    
    def find_top_params(
        self,
        results: pd.DataFrame,
        metric: str = 'sharpe_ratio',
        top_n: int = 10
    ) -> pd.DataFrame:
        """找出Top N参数组合
        
        Args:
            results: 分析结果
            metric: 排序指标
            top_n: 数量
            
        Returns:
            Top N参数组合
        """
        if results.empty or metric not in results.columns:
            return pd.DataFrame()
        
        return results.nlargest(top_n, metric)
    
    def analyze_sensitivity(
        self,
        results: pd.DataFrame,
        metric: str = 'sharpe_ratio'
    ) -> pd.DataFrame:
        """分析参数敏感�?
        
        Args:
            results: 分析结果
            metric: 分析指标
            
        Returns:
            各参数的敏感性统�?
        """
        if results.empty:
            return pd.DataFrame()
        
        sensitivity = []
        
        for param_name in self.param_ranges.keys():
            if param_name not in results.columns:
                continue
            
            # 按参数值分组计算指标均�?
            grouped = results.groupby(param_name)[metric].agg(['mean', 'std', 'min', 'max'])
            
            # 计算敏感性系数（变异系数�?
            cv = grouped['std'] / grouped['mean'].abs()
            
            sensitivity.append({
                'param': param_name,
                'mean': grouped['mean'].mean(),
                'std': grouped['std'].mean(),
                'min': grouped['min'].min(),
                'max': grouped['max'].max(),
                'sensitivity': cv.mean(),  # 敏感性系�?
            })
        
        return pd.DataFrame(sensitivity).sort_values('sensitivity', ascending=False)
