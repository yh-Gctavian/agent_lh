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
    输出最优参数组合
    """
    
    def __init__(self, param_ranges: Dict[str, List[Any]] = None):
        """初始化
        
        Args:
            param_ranges: 参数范围，如 {'kdj_j_threshold': [15, 20, 25]}
        """
        self.param_ranges = param_ranges or {}
    
    def grid_search(
        self,
        backtest_func: Callable,
        base_params: Dict[str, Any] = None
    ) -> pd.DataFrame:
        """网格搜索
        
        Args:
            backtest_func: 回测函数，接受参数字典返回结果字典
            base_params: 基础参数
            
        Returns:
            各参数组合的回测结果
        """
        base_params = base_params or {}
        
        # 生成参数组合
        combinations = self._generate_combinations()
        
        logger.info(f"开始网格搜索: {len(combinations)}组参数")
        
        results = []
        for i, params in enumerate(combinations):
            logger.info(f"进度: {i+1}/{len(combinations)}")
            
            try:
                # 合并参数
                full_params = {**base_params, **params}
                
                # 运行回测
                metrics = backtest_func(full_params)
                
                # 记录结果
                result = {**params}
                if isinstance(metrics, dict):
                    result.update(metrics)
                results.append(result)
                
            except Exception as e:
                logger.warning(f"参数组合{params}失败: {e}")
                results.append({**params, 'error': str(e)})
        
        return pd.DataFrame(results)
    
    def _generate_combinations(self) -> List[Dict]:
        """生成参数组合
        
        Returns:
            参数组合列表
        """
        if not self.param_ranges:
            return [{}]
        
        # 获取参数名和值列表
        keys = list(self.param_ranges.keys())
        values = [self.param_ranges[k] for k in keys]
        
        # 生成所有组合
        combinations = []
        for combo in product(*values):
            combinations.append(dict(zip(keys, combo)))
        
        return combinations
    
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
            最优参数和结果
        """
        if results.empty or metric not in results.columns:
            return {}
        
        # 排除错误结果
        valid = results[~results.get('error', pd.Series()).notna()]
        
        if valid.empty:
            return {}
        
        # 找最优
        if maximize:
            best_idx = valid[metric].idxmax()
        else:
            best_idx = valid[metric].idxmin()
        
        return valid.loc[best_idx].to_dict()
    
    def one_dim_sensitivity(
        self,
        backtest_func: Callable,
        param_name: str,
        param_values: List[Any],
        base_params: Dict = None
    ) -> pd.DataFrame:
        """单参数敏感性分析
        
        Args:
            backtest_func: 回测函数
            param_name: 参数名
            param_values: 参数值列表
            base_params: 基础参数
            
        Returns:
            敏感性分析结果
        """
        base_params = base_params or {}
        
        results = []
        for value in param_values:
            params = {**base_params, param_name: value}
            
            try:
                metrics = backtest_func(params)
                result = {param_name: value}
                if isinstance(metrics, dict):
                    result.update(metrics)
                results.append(result)
            except Exception as e:
                logger.warning(f"{param_name}={value} 失败: {e}")
        
        return pd.DataFrame(results)
    
    def plot_sensitivity(
        self,
        results: pd.DataFrame,
        param_name: str,
        metric: str = 'sharpe_ratio'
    ):
        """绘制敏感性分析图
        
        Args:
            results: 分析结果
            param_name: 参数名
            metric: 指标名
        """
        try:
            import matplotlib.pyplot as plt
            
            fig, ax = plt.subplots(figsize=(10, 6))
            
            ax.plot(results[param_name], results[metric], 'b-o')
            ax.set_xlabel(param_name)
            ax.set_ylabel(metric)
            ax.set_title(f'Sensitivity: {param_name} vs {metric}')
            
            plt.tight_layout()
            plt.savefig(f'sensitivity_{param_name}.png')
            plt.close()
            
            logger.info(f"敏感性图已保存: sensitivity_{param_name}.png")
            
        except Exception as e:
            logger.warning(f"绘图失败: {e}")
    
    def get_param_importance(
        self,
        results: pd.DataFrame,
        metric: str = 'sharpe_ratio'
    ) -> pd.Series:
        """计算参数重要性
        
        通过各参数变化对指标的影响程度衡量
        
        Args:
            results: 分析结果
            metric: 目标指标
            
        Returns:
            参数重要性排序
        """
        if results.empty:
            return pd.Series()
        
        importance = {}
        
        for param in self.param_ranges.keys():
            if param not in results.columns:
                continue
            
            # 计算该参数不同取值下指标的方差
            grouped = results.groupby(param)[metric].mean()
            variance = grouped.var()
            
            importance[param] = variance
        
        return pd.Series(importance).sort_values(ascending=False)