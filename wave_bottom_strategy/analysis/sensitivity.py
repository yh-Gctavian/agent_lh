# -*- coding: utf-8 -*-
"""参数敏感性分析"""

from typing import Dict, List, Any, Callable
import pandas as pd


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
    
    def run_analysis(
        self,
        backtest_func: Callable,
        base_params: Dict[str, Any]
    ) -> pd.DataFrame:
        """运行敏感性分析
        
        Args:
            backtest_func: 回测函数
            base_params: 基础参数
            
        Returns:
            各参数组合的回测结果
        """
        results = []
        
        # 生成参数组合
        param_combinations = self._generate_combinations()
        
        for params in param_combinations:
            # 合并参数
            full_params = {**base_params, **params}
            
            # 运行回测
            try:
                metrics = backtest_func(full_params)
                results.append({
                    **params,
                    **metrics
                })
            except Exception as e:
                results.append({
                    **params,
                    'error': str(e)
                })
        
        return pd.DataFrame(results)
    
    def _generate_combinations(self) -> List[Dict]:
        """生成参数组合
        
        Returns:
            参数组合列表
        """
        # TODO: 实现参数组合生成逻辑
        # 使用 itertools.product 或递归
        raise NotImplementedError
    
    def find_optimal_params(
        self,
        results: pd.DataFrame,
        metric: str = 'sharpe_ratio'
    ) -> Dict:
        """找出最优参数
        
        Args:
            results: 分析结果
            metric: 优化指标
            
        Returns:
            最优参数
        """
        best_row = results.loc[results[metric].idxmax()]
        return best_row.to_dict()