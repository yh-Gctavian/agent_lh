# -*- coding: utf-8 -*-
"""参数敏感性分析"""

from typing import Dict, List, Any, Callable
import pandas as pd
import numpy as np
from itertools import product

from utils.logger import get_logger

logger = get_logger('sensitivity_analysis')


class SensitivityAnalysis:
    """参数敏感性分析"""
    
    def __init__(self, param_ranges: Dict[str, List[Any]]):
        """初始化
        
        Args:
            param_ranges: 参数范围，如 {'min_score': [50, 60, 70], 'kdj_threshold': [15, 20, 25]}
        """
        self.param_ranges = param_ranges
    
    def generate_combinations(self) -> List[Dict]:
        """生成参数组合"""
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
        combinations = self.generate_combinations()
        results = []
        
        for i, params in enumerate(combinations):
            logger.info(f"进度: {i+1}/{len(combinations)} - {params}")
            
            try:
                full_params = {**(base_params or {}), **params}
                metrics = backtest_func(full_params)
                
                result = {
                    **params,
                    **metrics
                }
                results.append(result)
                
            except Exception as e:
                logger.warning(f"参数组合失败: {params}, {e}")
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
            最优参数
        """
        valid = results[~results.get('error', pd.Series()).notna()]
        
        if valid.empty or metric not in valid.columns:
            return {}
        
        if maximize:
            best_idx = valid[metric].idxmax()
        else:
            best_idx = valid[metric].idxmin()
        
        return valid.loc[best_idx].to_dict()
    
    def get_top_n(
        self,
        results: pd.DataFrame,
        metric: str = 'sharpe_ratio',
        n: int = 5
    ) -> pd.DataFrame:
        """获取Top N参数组合"""
        valid = results[~results.get('error', pd.Series()).notna()]
        
        if valid.empty or metric not in valid.columns:
            return pd.DataFrame()
        
        return valid.nlargest(n, metric)


def run_walk_forward(
    backtest_func: Callable,
    train_periods: List[tuple],
    test_periods: List[tuple],
    params: Dict
) -> pd.DataFrame:
    """Walk-Forward验证
    
    Args:
        backtest_func: 回测函数
        train_periods: 训练期列表
        test_periods: 测试期列表
        params: 参数
        
    Returns:
        验证结果
    """
    results = []
    
    for i, (train, test) in enumerate(zip(train_periods, test_periods)):
        logger.info(f"Walk-Forward: {i+1}/{len(train_periods)}")
        
        try:
            # 训练期优化
            train_result = backtest_func({**params, 'start': train[0], 'end': train[1]})
            
            # 测试期验证
            test_result = backtest_func({**params, 'start': test[0], 'end': test[1]})
            
            results.append({
                'fold': i + 1,
                'train_period': train,
                'test_period': test,
                'train_return': train_result.get('total_return', 0),
                'test_return': test_result.get('total_return', 0)
            })
            
        except Exception as e:
            logger.warning(f"Fold {i+1} 失败: {e}")
    
    return pd.DataFrame(results)