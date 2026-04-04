# -*- coding: utf-8 -*-
"""参数敏感性分析"""

from typing import Dict, List, Any, Callable
import pandas as pd
import numpy as np
from itertools import product

from utils.logger import get_logger

logger = get_logger('sensitivity')


class SensitivityAnalysis:
    """参数敏感性分析
    
    分析单个参数变化对策略表现的影响
    """
    
    def __init__(self, base_params: Dict[str, Any]):
        """初始化
        
        Args:
            base_params: 基准参数
        """
        self.base_params = base_params
        self.results: List[Dict] = []
    
    def analyze_single(
        self,
        param_name: str,
        param_range: List[Any],
        backtest_func: Callable,
        metric: str = 'total_return'
    ) -> pd.DataFrame:
        """单参数敏感性分析
        
        Args:
            param_name: 参数名
            param_range: 参数范围
            backtest_func: 回测函数
            metric: 评估指标
            
        Returns:
            分析结果
        """
        logger.info(f"单参数敏感性分析: {param_name}, 范围: {param_range}")
        
        results = []
        
        for value in param_range:
            # 构建参数
            params = self.base_params.copy()
            params[param_name] = value
            
            # 执行回测
            try:
                result = backtest_func(params)
                
                results.append({
                    'param_name': param_name,
                    'param_value': value,
                    'metric': result.get(metric, 0),
                    **{k: v for k, v in result.items() if k != metric}
                })
                
            except Exception as e:
                logger.warning(f"参数 {param_name}={value} 回测失败: {e}")
        
        df = pd.DataFrame(results)
        
        if not df.empty:
            # 计算敏感性指标
            df['sensitivity'] = df['metric'].std() / df['metric'].mean() if df['metric'].mean() != 0 else 0
        
        return df
    
    def analyze_multiple(
        self,
        param_ranges: Dict[str, List[Any]],
        backtest_func: Callable,
        metric: str = 'total_return'
    ) -> pd.DataFrame:
        """多参数敏感性分析
        
        Args:
            param_ranges: {参数名: 参数范围}
            backtest_func: 回测函数
            metric: 评估指标
            
        Returns:
            分析结果
        """
        logger.info(f"多参数敏感性分析: {list(param_ranges.keys())}")
        
        results = []
        
        # 生成参数组合
        param_names = list(param_ranges.keys())
        param_values = list(param_ranges.values())
        combinations = list(product(*param_values))
        
        total = len(combinations)
        
        for i, combo in enumerate(combinations):
            if i % 10 == 0:
                logger.info(f"进度: {i+1}/{total}")
            
            params = self.base_params.copy()
            for name, value in zip(param_names, combo):
                params[name] = value
            
            try:
                result = backtest_func(params)
                
                row = {name: value for name, value in zip(param_names, combo)}
                row['metric'] = result.get(metric, 0)
                row.update({k: v for k, v in result.items() if k != metric})
                
                results.append(row)
                
            except Exception as e:
                logger.warning(f"参数组合失败: {combo}, {e}")
        
        return pd.DataFrame(results)
    
    def find_optimal(
        self,
        df: pd.DataFrame,
        metric: str = 'metric',
        top_n: int = 5
    ) -> pd.DataFrame:
        """找出最优参数
        
        Args:
            df: 分析结果
            metric: 指标列名
            top_n: 返回数量
            
        Returns:
            Top N参数组合
        """
        return df.nlargest(top_n, metric)
    
    def get_sensitivity_rank(
        self,
        param_names: List[str],
        param_ranges: Dict[str, List],
        backtest_func: Callable,
        metric: str = 'total_return'
    ) -> pd.DataFrame:
        """获取参数敏感性排名
        
        Args:
            param_names: 参数名列表
            param_ranges: 参数范围
            backtest_func: 回测函数
            metric: 评估指标
            
        Returns:
            敏感性排名
        """
        sensitivities = []
        
        for param_name in param_names:
            df = self.analyze_single(
                param_name,
                param_ranges.get(param_name, []),
                backtest_func,
                metric
            )
            
            if not df.empty and 'sensitivity' in df.columns:
                sensitivities.append({
                    'param_name': param_name,
                    'sensitivity': df['sensitivity'].iloc[0],
                    'value_range': f"{df['metric'].min():.4f} ~ {df['metric'].max():.4f}",
                    'optimal_value': df.loc[df['metric'].idxmax(), 'param_value']
                })
        
        result = pd.DataFrame(sensitivities)
        result = result.sort_values('sensitivity', ascending=False)
        
        return result


class GridSearch:
    """网格搜索
    
    遍历参数空间，找出最优组合
    """
    
    def __init__(
        self,
        param_grid: Dict[str, List],
        backtest_func: Callable,
        metric: str = 'sharpe'
    ):
        """初始化
        
        Args:
            param_grid: 参数网格
            backtest_func: 回测函数
            metric: 优化指标
        """
        self.param_grid = param_grid
        self.backtest_func = backtest_func
        self.metric = metric
        self.results: List[Dict] = []
    
    def run(self) -> pd.DataFrame:
        """执行网格搜索
        
        Returns:
            搜索结果
        """
        logger.info("开始网格搜索...")
        
        param_names = list(self.param_grid.keys())
        param_values = list(self.param_grid.values())
        combinations = list(product(*param_values))
        
        total = len(combinations)
        logger.info(f"参数组合数: {total}")
        
        results = []
        
        for i, combo in enumerate(combinations):
            if i % 10 == 0:
                logger.info(f"进度: {i+1}/{total}")
            
            params = dict(zip(param_names, combo))
            
            try:
                result = self.backtest_func(params)
                
                row = params.copy()
                row[self.metric] = result.get(self.metric, 0)
                row.update({k: v for k, v in result.items() if k != self.metric})
                
                results.append(row)
                
            except Exception as e:
                logger.warning(f"组合 {combo} 失败: {e}")
        
        self.results = results
        return pd.DataFrame(results)
    
    def get_best(self) -> Dict:
        """获取最优参数
        
        Returns:
            最优参数
        """
        if not self.results:
            return {}
        
        df = pd.DataFrame(self.results)
        best_idx = df[self.metric].idxmax()
        
        return df.loc[best_idx].to_dict()