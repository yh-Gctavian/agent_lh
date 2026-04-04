# -*- coding: utf-8 -*-
"""Walk-Forward验证"""

from typing import Dict, List, Any, Callable, Tuple
import pandas as pd
import numpy as np
from datetime import datetime

from wave_bottom_strategy.utils.logger import get_logger

logger = get_logger('walk_forward')


class WalkForwardValidator:
    """Walk-Forward验证
    
    样本内训练，样本外测试
    防止过拟合
    """
    
    def __init__(
        self,
        backtest_func: Callable,
        train_start: str = '2020-01-01',
        train_end: str = '2023-12-31',
        test_start: str = '2024-01-01',
        test_end: str = '2025-12-31'
    ):
        """
        Args:
            backtest_func: 回测函数
            train_start: 训练开始日期
            train_end: 训练结束日期
            test_start: 测试开始日期
            test_end: 测试结束日期
        """
        self.backtest_func = backtest_func
        self.train_period = (train_start, train_end)
        self.test_period = (test_start, test_end)
    
    def validate(
        self,
        params: Dict[str, Any],
        metrics: List[str] = None
    ) -> Dict[str, Any]:
        """执行Walk-Forward验证
        
        Args:
            params: 参数组合
            metrics: 评估指标列表
            
        Returns:
            训练期和测试期的绩效对比
        """
        metrics = metrics or ['total_return', 'sharpe_ratio', 'max_drawdown']
        
        # 训练期回测
        logger.info(f"训练期回测: {self.train_period}")
        train_params = params.copy()
        train_params['start_date'] = self.train_period[0]
        train_params['end_date'] = self.train_period[1]
        
        train_results = self.backtest_func(train_params)
        
        # 测试期回测
        logger.info(f"测试期回测: {self.test_period}")
        test_params = params.copy()
        test_params['start_date'] = self.test_period[0]
        test_params['end_date'] = self.test_period[1]
        
        test_results = self.backtest_func(test_params)
        
        # 对比
        comparison = {
            'params': params,
            'train_period': self.train_period,
            'test_period': self.test_period,
        }
        
        for metric in metrics:
            train_value = train_results.get(metric, 0)
            test_value = test_results.get(metric, 0)
            
            comparison[f'train_{metric}'] = train_value
            comparison[f'test_{metric}'] = test_value
            
            # 衰减率（测试期相对训练期的表现衰减）
            if train_value != 0:
                decay = (test_value - train_value) / abs(train_value)
                comparison[f'{metric}_decay'] = decay
            else:
                comparison[f'{metric}_decay'] = 0
        
        return comparison
    
    def validate_multiple(
        self,
        params_list: List[Dict[str, Any]]
    ) -> pd.DataFrame:
        """批量验证多个参数组合
        
        Args:
            params_list: 参数组合列表
            
        Returns:
            验证结果对比表
        """
        results = []
        
        for i, params in enumerate(params_list):
            logger.info(f"验证参数组合 {i+1}/{len(params_list)}")
            
            comparison = self.validate(params)
            results.append(comparison)
        
        return pd.DataFrame(results)
    
    def find_robust_params(
        self,
        validation_results: pd.DataFrame,
        metric: str = 'sharpe_ratio',
        max_decay: float = 0.3
    ) -> pd.DataFrame:
        """找出稳健参数（测试期表现衰减不超过阈值）
        
        Args:
            validation_results: 验证结果
            metric: 评估指标
            max_decay: 最大允许衰减率
            
        Returns:
            稳健参数组合
        """
        decay_col = f'{metric}_decay'
        test_col = f'test_{metric}'
        
        # 筛选衰减率在阈值内的
        robust = validation_results[
            validation_results[decay_col] >= -max_decay
        ]
        
        # 按测试期表现排序
        robust = robust.sort_values(test_col, ascending=False)
        
        logger.info(f"稳健参数数量: {len(robust)}/{len(validation_results)}")
        
        return robust
    
    def rolling_validate(
        self,
        params: Dict[str, Any],
        window_size: int = 252,  # 一年
        step: int = 63           # 一季度
    ) -> pd.DataFrame:
        """滚动Walk-Forward验证
        
        Args:
            params: 参数
            window_size: 训练窗口大小
            step: 滚动步长
            
        Returns:
            各窗口的验证结果
        """
        results = []
        
        # 简化实现：假设按年滚动
        years = [2020, 2021, 2022, 2023, 2024]
        
        for i, year in enumerate(years[:-1]):
            train_start = f'{year}-01-01'
            train_end = f'{year}-12-31'
            test_year = years[i + 1]
            test_start = f'{test_year}-01-01'
            test_end = f'{test_year}-12-31'
            
            validator = WalkForwardValidator(
                self.backtest_func,
                train_start, train_end,
                test_start, test_end
            )
            
            result = validator.validate(params)
            result['train_year'] = year
            result['test_year'] = test_year
            results.append(result)
        
        return pd.DataFrame(results)


class ParameterStabilityAnalyzer:
    """参数稳定性分析
    
    检验参数在不同时期的表现稳定性
    """
    
    def __init__(self, backtest_func: Callable):
        self.backtest_func = backtest_func
    
    def analyze(
        self,
        params: Dict[str, Any],
        periods: List[Tuple[str, str]]
    ) -> pd.DataFrame:
        """分析参数在各时期的稳定性
        
        Args:
            params: 参数
            periods: 时期列表 [(start, end), ...]
            
        Returns:
            各时期表现
        """
        results = []
        
        for start, end in periods:
            test_params = params.copy()
            test_params['start_date'] = start
            test_params['end_date'] = end
            
            metrics = self.backtest_func(test_params)
            metrics['period'] = f'{start}~{end}'
            results.append(metrics)
        
        df = pd.DataFrame(results)
        
        # 计算稳定性指标
        stability = {
            'return_std': df['total_return'].std() if 'total_return' in df else 0,
            'sharpe_std': df['sharpe_ratio'].std() if 'sharpe_ratio' in df else 0,
            'return_mean': df['total_return'].mean() if 'total_return' in df else 0,
            'sharpe_mean': df['sharpe_ratio'].mean() if 'sharpe_ratio' in df else 0,
        }
        
        df.attrs['stability'] = stability
        
        return df