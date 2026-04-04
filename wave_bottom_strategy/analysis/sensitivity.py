# -*- coding: utf-8 -*-
"""参数敏感性分析"""

from typing import Dict, List, Any, Callable
import pandas as pd
import numpy as np
from itertools import product

from wave_bottom_strategy.utils.logger import get_logger

logger = get_logger('sensitivity_analysis')


class SensitivityAnalysis:
    """参数敏感性分析
    
    测试单个参数变化对策略表现的影响
    """
    
    def __init__(self, param_ranges: Dict[str, List[Any]]):
        """初始化
        
        Args:
            param_ranges: 参数范围，如 {'kdj_j_threshold': [10, 15, 20, 25, 30]}
        """
        self.param_ranges = param_ranges
        self.results: pd.DataFrame = None
    
    def run_single_param(
        self,
        param_name: str,
        param_values: List[Any],
        backtest_func: Callable,
        base_params: Dict[str, Any]
    ) -> pd.DataFrame:
        """单参数敏感性分析
        
        Args:
            param_name: 参数名
            param_values: 参数值列表
            backtest_func: 回测函数
            base_params: 基础参数
            
        Returns:
            敏感性分析结果
        """
        logger.info(f"单参数敏感性分析: {param_name}, 值: {param_values}")
        
        results = []
        
        for value in param_values:
            # 更新参数
            params = {**base_params, param_name: value}
            
            try:
                # 运行回测
                metrics = backtest_func(params)
                
                results.append({
                    param_name: value,
                    'total_return': metrics.get('total_return', 0),
                    'sharpe_ratio': metrics.get('sharpe_ratio', 0),
                    'max_drawdown': metrics.get('max_drawdown', 0),
                    'win_rate': metrics.get('win_rate', 0),
                })
                
            except Exception as e:
                logger.warning(f"参数 {param_name}={value} 回测失败: {e}")
        
        self.results = pd.DataFrame(results)
        return self.results
    
    def run_all_params(
        self,
        backtest_func: Callable,
        base_params: Dict[str, Any]
    ) -> Dict[str, pd.DataFrame]:
        """对所有参数运行敏感性分析
        
        Args:
            backtest_func: 回测函数
            base_params: 基础参数
            
        Returns:
            {参数名: 敏感性结果}
        """
        all_results = {}
        
        for param_name, param_values in self.param_ranges.items():
            logger.info(f"分析参数: {param_name}")
            result = self.run_single_param(param_name, param_values, backtest_func, base_params)
            all_results[param_name] = result
        
        return all_results
    
    def identify_key_params(
        self,
        results: Dict[str, pd.DataFrame],
        metric: str = 'sharpe_ratio'
    ) -> pd.DataFrame:
        """识别关键参数（敏感性高的参数）
        
        Args:
            results: 敏感性分析结果
            metric: 评估指标
            
        Returns:
            参数敏感性排序
        """
        sensitivity_scores = []
        
        for param_name, df in results.items():
            if df.empty or metric not in df.columns:
                continue
            
            # 计算敏感性系数：指标变化幅度 / 参数变化幅度
            values = df[metric].values
            if len(values) < 2:
                continue
            
            # 使用变异系数作为敏感性指标
            cv = df[metric].std() / df[metric].mean() if df[metric].mean() != 0 else 0
            
            sensitivity_scores.append({
                'param': param_name,
                'sensitivity_cv': cv,
                'min_value': df[metric].min(),
                'max_value': df[metric].max(),
                'range': df[metric].max() - df[metric].min()
            })
        
        result_df = pd.DataFrame(sensitivity_scores)
        result_df = result_df.sort_values('sensitivity_cv', ascending=False)
        
        return result_df
    
    def get_optimal_range(
        self,
        result: pd.DataFrame,
        param_name: str,
        metric: str = 'sharpe_ratio',
        top_n: int = 3
    ) -> List[Any]:
        """获取最优参数范围
        
        Args:
            result: 单参数分析结果
            param_name: 参数名
            metric: 优化指标
            top_n: 返回top N个参数值
            
        Returns:
            最优参数值列表
        """
        if result.empty or metric not in result.columns:
            return []
        
        top = result.nlargest(top_n, metric)
        return top[param_name].tolist()


class GridSearch:
    """网格搜索
    
    遍历所有参数组合，找到最优参数
    """
    
    def __init__(self, param_ranges: Dict[str, List[Any]]):
        """初始化
        
        Args:
            param_ranges: 参数范围
        """
        self.param_ranges = param_ranges
        self.results: pd.DataFrame = None
    
    def get_total_combinations(self) -> int:
        """获取总组合数"""
        total = 1
        for values in self.param_ranges.values():
            total *= len(values)
        return total
    
    def generate_combinations(self) -> List[Dict[str, Any]]:
        """生成所有参数组合
        
        Returns:
            参数组合列表
        """
        keys = list(self.param_ranges.keys())
        values = list(self.param_ranges.values())
        
        combinations = []
        for combo in product(*values):
            combinations.append(dict(zip(keys, combo)))
        
        return combinations
    
    def run(
        self,
        backtest_func: Callable,
        parallel: bool = False,
        n_jobs: int = 4
    ) -> pd.DataFrame:
        """运行网格搜索
        
        Args:
            backtest_func: 回测函数
            parallel: 是否并行
            n_jobs: 并行进程数
            
        Returns:
            搜索结果
        """
        combinations = self.generate_combinations()
        total = len(combinations)
        
        logger.info(f"网格搜索开始: {total}个组合")
        
        results = []
        
        for i, params in enumerate(combinations):
            if (i + 1) % 10 == 0:
                logger.info(f"进度: {i+1}/{total}")
            
            try:
                metrics = backtest_func(params)
                
                results.append({
                    **params,
                    'total_return': metrics.get('total_return', 0),
                    'sharpe_ratio': metrics.get('sharpe_ratio', 0),
                    'max_drawdown': metrics.get('max_drawdown', 0),
                    'win_rate': metrics.get('win_rate', 0),
                })
                
            except Exception as e:
                logger.warning(f"参数组合失败: {params}, {e}")
        
        self.results = pd.DataFrame(results)
        logger.info(f"网格搜索完成: {len(results)}个有效结果")
        
        return self.results
    
    def get_top_combinations(
        self,
        metric: str = 'sharpe_ratio',
        top_n: int = 10
    ) -> pd.DataFrame:
        """获取最优参数组合
        
        Args:
            metric: 优化指标
            top_n: 返回数量
            
        Returns:
            Top N参数组合
        """
        if self.results is None or self.results.empty:
            return pd.DataFrame()
        
        return self.results.nlargest(top_n, metric)


class WalkForwardValidation:
    """Walk-Forward验证
    
    滚动窗口验证，防止过拟合
    """
    
    def __init__(
        self,
        train_period: int = 3 * 252,  # 3年交易日
        test_period: int = 1 * 252,   # 1年交易日
        step: int = 1 * 252           # 滚动步长
    ):
        """初始化
        
        Args:
            train_period: 训练期长度（交易日）
            test_period: 测试期长度（交易日）
            step: 滚动步长
        """
        self.train_period = train_period
        self.test_period = test_period
        self.step = step
    
    def generate_windows(
        self,
        start_date: str,
        end_date: str
    ) -> List[Dict[str, str]]:
        """生成滚动窗口
        
        Args:
            start_date: 总开始日期
            end_date: 总结束日期
            
        Returns:
            窗口列表 [{'train_start': ..., 'train_end': ..., 'test_start': ..., 'test_end': ...}]
        """
        dates = pd.date_range(start_date, end_date, freq='B')  # 工作日
        
        windows = []
        i = 0
        
        while i + self.train_period + self.test_period <= len(dates):
            train_start = dates[i].strftime('%Y-%m-%d')
            train_end = dates[i + self.train_period - 1].strftime('%Y-%m-%d')
            test_start = dates[i + self.train_period].strftime('%Y-%m-%d')
            test_end = dates[i + self.train_period + self.test_period - 1].strftime('%Y-%m-%d')
            
            windows.append({
                'train_start': train_start,
                'train_end': train_end,
                'test_start': test_start,
                'test_end': test_end
            })
            
            i += self.step
        
        logger.info(f"生成{len(windows)}个滚动窗口")
        return windows
    
    def run(
        self,
        start_date: str,
        end_date: str,
        optimize_func: Callable,
        backtest_func: Callable
    ) -> pd.DataFrame:
        """运行Walk-Forward验证
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            optimize_func: 参数优化函数
            backtest_func: 回测函数
            
        Returns:
            验证结果
        """
        windows = self.generate_windows(start_date, end_date)
        
        results = []
        
        for i, window in enumerate(windows):
            logger.info(f"Walk-Forward第{i+1}/{len(windows)}轮")
            
            # 训练期优化参数
            optimal_params = optimize_func(window['train_start'], window['train_end'])
            
            # 测试期验证
            test_metrics = backtest_func(optimal_params, window['test_start'], window['test_end'])
            
            results.append({
                'round': i + 1,
                **window,
                'test_return': test_metrics.get('total_return', 0),
                'test_sharpe': test_metrics.get('sharpe_ratio', 0),
                'test_drawdown': test_metrics.get('max_drawdown', 0),
                'optimal_params': optimal_params
            })
        
        return pd.DataFrame(results)
    
    def calculate_oos_metrics(self, results: pd.DataFrame) -> Dict:
        """计算样本外指标
        
        Args:
            results: Walk-Forward结果
            
        Returns:
            样本外统计指标
        """
        if results.empty:
            return {}
        
        return {
            'avg_oos_return': results['test_return'].mean(),
            'avg_oos_sharpe': results['test_sharpe'].mean(),
            'avg_oos_drawdown': results['test_drawdown'].mean(),
            'oos_return_std': results['test_return'].std(),
            'positive_rounds': (results['test_return'] > 0).sum(),
            'total_rounds': len(results),
            'win_rate': (results['test_return'] > 0).mean()
        }