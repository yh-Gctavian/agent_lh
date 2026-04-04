# -*- coding: utf-8 -*-
"""参数敏感性分析"""

from typing import Dict, List, Any, Callable
import pandas as pd
import itertools

from utils.logger import get_logger

logger = get_logger('sensitivity')


class SensitivityAnalysis:
    """参数敏感性分析"""
    
    def __init__(self, param_ranges: Dict[str, List[Any]]):
        """初始化
        
        Args:
            param_ranges: 参数范围，如 {'kdj_n': [5, 9, 14]}
        """
        self.param_ranges = param_ranges
    
    def grid_search(
        self,
        backtest_func: Callable,
        base_params: Dict[str, Any] = None
    ) -> pd.DataFrame:
        """网格搜索
        
        Args:
            backtest_func: 回测函数
            base_params: 基础参数
            
        Returns:
            各参数组合的结果
        """
        results = []
        combinations = self._generate_combinations()
        
        logger.info(f"网格搜索: {len(combinations)}组参数")
        
        for i, params in enumerate(combinations):
            logger.debug(f"进度: {i+1}/{len(combinations)}")
            
            try:
                full_params = {**(base_params or {}), **params}
                metrics = backtest_func(full_params)
                
                results.append({
                    **params,
                    **metrics
                })
            except Exception as e:
                logger.warning(f"参数{params}失败: {e}")
        
        return pd.DataFrame(results)
    
    def _generate_combinations(self) -> List[Dict]:
        """生成参数组合"""
        keys = list(self.param_ranges.keys())
        values = list(self.param_ranges.values())
        
        combinations = []
        for combo in itertools.product(*values):
            combinations.append(dict(zip(keys, combo)))
        
        return combinations
    
    def find_optimal(
        self,
        results: pd.DataFrame,
        metric: str = 'sharpe_ratio',
        top_n: int = 5
    ) -> pd.DataFrame:
        """找出最优参数
        
        Args:
            results: 分析结果
            metric: 优化指标
            top_n: 返回数量
            
        Returns:
            最优参数组合
        """
        sorted_df = results.sort_values(metric, ascending=False)
        return sorted_df.head(top_n)
    
    def one_way_analysis(
        self,
        results: pd.DataFrame,
        param_name: str,
        metric: str = 'sharpe_ratio'
    ) -> pd.DataFrame:
        """单因素分析
        
        Args:
            results: 结果
            param_name: 参数名
            metric: 指标
            
        Returns:
            该参数各取值的平均表现
        """
        if param_name not in results.columns:
            return pd.DataFrame()
        
        return results.groupby(param_name)[metric].agg(['mean', 'std', 'count'])