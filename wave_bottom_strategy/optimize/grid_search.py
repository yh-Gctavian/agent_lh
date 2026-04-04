# -*- coding: utf-8 -*-
"""网格搜索参数优化"""

from typing import Dict, List, Any, Callable
import pandas as pd
import itertools
from datetime import datetime

from wave_bottom_strategy.utils.logger import get_logger

logger = get_logger('grid_search')


class GridSearchOptimizer:
    """网格搜索参数优化�?
    
    在参数空间中搜索最优组�?
    """
    
    def __init__(self, param_grid: Dict[str, List[Any]]):
        """
        Args:
            param_grid: 参数网格，如 {'kdj_n': [5, 9, 14], 'min_score': [60, 70, 80]}
        """
        self.param_grid = param_grid
        self.results: List[Dict] = []
    
    def fit(
        self,
        backtest_func: Callable,
        metric: str = 'sharpe_ratio'
    ) -> Dict:
        """执行网格搜索
        
        Args:
            backtest_func: 回测函数，接受参数dict返回指标dict
            metric: 优化目标指标
            
        Returns:
            最优参数组�?
        """
        # 生成所有参数组�?
        keys = list(self.param_grid.keys())
        values = list(self.param_grid.values())
        combinations = list(itertools.product(*values))
        
        logger.info(f"开始网格搜�? {len(combinations)}组参�?)
        
        for i, combo in enumerate(combinations):
            params = dict(zip(keys, combo))
            
            logger.info(f"[{i+1}/{len(combinations)}] 测试: {params}")
            
            try:
                # 执行回测
                metrics = backtest_func(params)
                
                # 记录结果
                result = {**params, **metrics}
                self.results.append(result)
                
            except Exception as e:
                logger.warning(f"参数组合失败: {params}, {e}")
        
        # 找出最优参�?
        if not self.results:
            return {}
        
        df = pd.DataFrame(self.results)
        best_idx = df[metric].idxmax()
        best_params = df.loc[best_idx].to_dict()
        
        logger.info(f"最优参�? {best_params}")
        
        return best_params
    
    def get_results(self) -> pd.DataFrame:
        """获取所有结�?""
        return pd.DataFrame(self.results)
    
    def get_top_n(self, n: int = 5, metric: str = 'sharpe_ratio') -> pd.DataFrame:
        """获取Top N参数组合"""
        df = pd.DataFrame(self.results)
        if df.empty:
            return df
        return df.nlargest(n, metric)


# 预设参数网格
DEFAULT_PARAM_GRID = {
    # KDJ参数
    'kdj_n': [9, 14],
    'kdj_threshold': [15, 20, 25],
    
    # 选股参数
    'min_score': [60, 70, 80],
    'max_positions': [5, 10, 15],
    
    # 仓位参数
    'position_size': [0.08, 0.10, 0.12],
    
    # 买卖参数
    'buy_threshold': [65, 70, 75],
    'sell_threshold': [30, 40, 50]
}
