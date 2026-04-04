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
    找出最优参数
    """
    
    def __init__(self, param_ranges: Dict[str, List[Any]]):
        """
        Args:
            param_ranges: 参数范围
                如 {'kdj_n': [5, 9, 14], 'min_score': [50, 60, 70]}
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
            backtest_func: 回测函数，接受参数字典，返回指标字典
            base_params: 基础参数（不变的部分）
            
        Returns:
            各参数组合的回测结果
        """
        results = []
        combinations = self.generate_combinations()
        
        for i, params in enumerate(combinations):
            logger.info(f"参数组合 {i+1}/{len(combinations)}: {params}")
            
            # 合并参数
            full_params = {**(base_params or {}), **params}
            
            try:
                # 运行回测
                metrics = backtest_func(full_params)
                
                # 记录结果
                result = {**params, **metrics}
                results.append(result)
                
            except Exception as e:
                logger.error(f"参数组合失败: {params}, {e}")
                results.append({**params, 'error': str(e)})
        
        return pd.DataFrame(results)
    
    def find_optimal(
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
            最优参数组合
        """
        # 过滤有效结果
        valid = results[results[metric].notna()]
        
        if valid.empty:
            return {}
        
        if maximize:
            best_idx = valid[metric].idxmax()
        else:
            best_idx = valid[metric].idxmin()
        
        best_row = valid.loc[best_idx]
        
        return best_row.to_dict()
    
    def analyze_sensitivity(
        self,
        results: pd.DataFrame,
        metric: str = 'sharpe_ratio'
    ) -> Dict[str, float]:
        """分析各参数敏感性
        
        计算各参数变化对指标的影响程度
        
        Args:
            results: 分析结果
            metric: 目标指标
            
        Returns:
            {参数名: 敏感性系数}
        """
        sensitivity = {}
        
        for param in self.param_ranges.keys():
            if param not in results.columns:
                continue
            
            # 按参数值分组计算指标均值
            grouped = results.groupby(param)[metric].mean()
            
            if len(grouped) > 1:
                # 计算变化范围
                sensitivity[param] = grouped.std() / abs(grouped.mean()) if grouped.mean() != 0 else 0
        
        return sensitivity
    
    def grid_search(
        self,
        backtest_func: Callable,
        param_grid: Dict[str, List[Any]],
        base_params: Dict = None,
        metric: str = 'sharpe_ratio'
    ) -> tuple:
        """网格搜索最优参数
        
        Args:
            backtest_func: 回测函数
            param_grid: 参数网格
            base_params: 基础参数
            metric: 优化指标
            
        Returns:
            (最优参数, 最优结果, 全部结果)
        """
        self.param_ranges = param_grid
        results = self.run_analysis(backtest_func, base_params)
        optimal = self.find_optimal(results, metric)
        
        return optimal, results.loc[results[metric].idxmax()] if metric in results.columns else {}, results


def default_param_ranges() -> Dict[str, List]:
    """默认参数范围
    
    Returns:
        默认参数范围字典
    """
    return {
        'min_score': [50, 60, 70, 80],
        'kdj_threshold': [10, 15, 20, 25],
        'stop_loss': [-0.03, -0.05, -0.07, -0.10],
        'take_profit': [0.10, 0.15, 0.20],
        'max_hold_days': [3, 5, 7, 10],
        'position_size': [0.05, 0.10, 0.15, 0.20]
    }