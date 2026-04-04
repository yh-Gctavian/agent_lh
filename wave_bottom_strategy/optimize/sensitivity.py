# -*- coding: utf-8 -*-
"""参数敏感性分�?""

from typing import Dict, List, Any, Callable
import pandas as pd
import numpy as np
from itertools import product

from utils.logger import get_logger

logger = get_logger('sensitivity')


class SensitivityAnalyzer:
    """参数敏感性分�?
    
    分析单个参数对策略绩效的影响
    """
    
    def __init__(self, backtest_func: Callable):
        """
        Args:
            backtest_func: 回测函数，接受参数dict，返回绩效dict
        """
        self.backtest_func = backtest_func
    
    def analyze_single(
        self,
        param_name: str,
        param_values: List[Any],
        base_params: Dict[str, Any]
    ) -> pd.DataFrame:
        """单参数敏感性分�?
        
        Args:
            param_name: 参数�?
            param_values: 参数值列�?
            base_params: 基础参数
            
        Returns:
            各参数值对应的绩效
        """
        results = []
        
        for value in param_values:
            params = base_params.copy()
            params[param_name] = value
            
            try:
                metrics = self.backtest_func(params)
                results.append({
                    param_name: value,
                    **metrics
                })
                logger.info(f"{param_name}={value}: 完成")
            except Exception as e:
                logger.warning(f"{param_name}={value}: 失败 - {e}")
        
        return pd.DataFrame(results)
    
    def analyze_multiple(
        self,
        param_ranges: Dict[str, List[Any]],
        base_params: Dict[str, Any]
    ) -> pd.DataFrame:
        """多参数敏感性分析（遍历所有组合）
        
        Args:
            param_ranges: {参数�? 参数值列表}
            base_params: 基础参数
            
        Returns:
            各参数组合对应的绩效
        """
        results = []
        
        # 生成所有组�?
        param_names = list(param_ranges.keys())
        param_value_lists = list(param_ranges.values())
        combinations = list(product(*param_value_lists))
        
        total = len(combinations)
        logger.info(f"参数组合总数: {total}")
        
        for i, combo in enumerate(combinations):
            params = base_params.copy()
            for name, value in zip(param_names, combo):
                params[name] = value
            
            try:
                metrics = self.backtest_func(params)
                result = dict(zip(param_names, combo))
                result.update(metrics)
                results.append(result)
                
                if (i + 1) % 10 == 0:
                    logger.info(f"进度: {i+1}/{total}")
                    
            except Exception as e:
                logger.warning(f"组合 {combo} 失败: {e}")
        
        return pd.DataFrame(results)
    
    def find_optimal(
        self,
        results: pd.DataFrame,
        metric: str = 'sharpe_ratio',
        top_n: int = 10
    ) -> pd.DataFrame:
        """找出最优参数组�?
        
        Args:
            results: 分析结果
            metric: 优化指标
            top_n: 返回数量
            
        Returns:
            Top N参数组合
        """
        return results.nlargest(top_n, metric)
    
    def plot_sensitivity(
        self,
        results: pd.DataFrame,
        param_name: str,
        metric: str = 'total_return'
    ):
        """绘制敏感性分析图
        
        Args:
            results: 分析结果
            param_name: 参数�?
            metric: 指标�?
        """
        try:
            import matplotlib.pyplot as plt
            
            plt.figure(figsize=(10, 6))
            plt.plot(results[param_name], results[metric], 'b-o')
            plt.xlabel(param_name)
            plt.ylabel(metric)
            plt.title(f'{param_name} Sensitivity Analysis')
            plt.grid(True)
            plt.savefig(f'{param_name}_sensitivity.png')
            plt.close()
            
            logger.info(f"敏感性分析图已保�? {param_name}_sensitivity.png")
        except Exception as e:
            logger.warning(f"绘图失败: {e}")


class GridSearchOptimizer:
    """网格搜索优化�?
    
    在参数空间中搜索最优组�?
    """
    
    def __init__(
        self,
        backtest_func: Callable,
        param_grid: Dict[str, List[Any]]
    ):
        """
        Args:
            backtest_func: 回测函数
            param_grid: 参数网格
        """
        self.backtest_func = backtest_func
        self.param_grid = param_grid
    
    def search(
        self,
        base_params: Dict[str, Any] = None,
        metric: str = 'sharpe_ratio'
    ) -> pd.DataFrame:
        """执行网格搜索
        
        Args:
            base_params: 基础参数
            metric: 优化指标
            
        Returns:
            搜索结果（按指标排序�?
        """
        base_params = base_params or {}
        
        analyzer = SensitivityAnalyzer(self.backtest_func)
        results = analyzer.analyze_multiple(self.param_grid, base_params)
        
        # 排序
        results = results.sort_values(metric, ascending=False)
        
        return results
    
    def get_best_params(
        self,
        results: pd.DataFrame,
        metric: str = 'sharpe_ratio'
    ) -> Dict[str, Any]:
        """获取最优参�?
        
        Args:
            results: 搜索结果
            metric: 优化指标
            
        Returns:
            最优参数组�?
        """
        if results.empty:
            return {}
        
        best_row = results.iloc[0]
        
        # 提取参数
        params = {}
        for col in self.param_grid.keys():
            if col in best_row:
                params[col] = best_row[col]
        
        return params
