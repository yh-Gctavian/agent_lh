# -*- coding: utf-8 -*-
"""Walk-Forward验证"""

from typing import Dict, List, Tuple, Callable
import pandas as pd
import numpy as np
from datetime import datetime

from utils.logger import get_logger

logger = get_logger('walk_forward')


class WalkForwardValidation:
    """Walk-Forward验证
    
    样本内训练找最优参数，样本外测试验证
    避免过拟合
    """
    
    def __init__(
        self,
        train_start: str = '2020-01-01',
        train_end: str = '2023-12-31',
        test_start: str = '2024-01-01',
        test_end: str = '2025-12-31',
        walk_forward_windows: int = 1
    ):
        """初始化
        
        Args:
            train_start: 训练集开始日期
            train_end: 训练集结束日期
            test_start: 测试集开始日期
            test_end: 测试集结束日期
            walk_forward_windows: 滚动窗口数
        """
        self.train_start = train_start
        self.train_end = train_end
        self.test_start = test_start
        self.test_end = test_end
        self.walk_forward_windows = walk_forward_windows
    
    def run(
        self,
        param_ranges: Dict[str, List],
        backtest_func: Callable,
        metric: str = 'total_return'
    ) -> Dict:
        """执行Walk-Forward验证
        
        Args:
            param_ranges: 参数范围
            backtest_func: 回测函数（接受params, start_date, end_date）
            metric: 评估指标
            
        Returns:
            验证结果
        """
        logger.info(f"Walk-Forward验证: 训练{self.train_start}-{self.train_end}, 测试{self.test_start}-{self.test_end}")
        
        # 1. 在训练集上找最优参数
        logger.info("阶段1: 训练集优化...")
        optimal_params = self._optimize_on_train(param_ranges, backtest_func, metric)
        
        # 2. 在测试集上验证
        logger.info("阶段2: 测试集验证...")
        test_result = self._validate_on_test(optimal_params, backtest_func)
        
        # 3. 计算过拟合程度
        train_result = backtest_func(optimal_params, self.train_start, self.train_end)
        overfitting_score = self._calc_overfitting(train_result, test_result, metric)
        
        result = {
            'optimal_params': optimal_params,
            'train_result': train_result,
            'test_result': test_result,
            'overfitting_score': overfitting_score,
            'train_period': f"{self.train_start} ~ {self.train_end}",
            'test_period': f"{self.test_start} ~ {self.test_end}"
        }
        
        logger.info(f"验证完成: 过拟合度={overfitting_score:.2%}")
        
        return result
    
    def _optimize_on_train(
        self,
        param_ranges: Dict[str, List],
        backtest_func: Callable,
        metric: str
    ) -> Dict:
        """在训练集上优化参数"""
        from itertools import product
        
        param_names = list(param_ranges.keys())
        param_values = list(param_ranges.values())
        combinations = list(product(*param_values))
        
        best_params = None
        best_score = -np.inf
        
        for combo in combinations:
            params = {name: value for name, value in zip(param_names, combo)}
            
            try:
                result = backtest_func(params, self.train_start, self.train_end)
                score = result.get(metric, 0)
                
                if score > best_score:
                    best_score = score
                    best_params = params
            except Exception as e:
                logger.warning(f"参数组合失败: {params}, {e}")
        
        logger.info(f"训练集最优: {best_params}, {metric}={best_score}")
        
        return best_params or {}
    
    def _validate_on_test(
        self,
        params: Dict,
        backtest_func: Callable
    ) -> Dict:
        """在测试集上验证"""
        try:
            result = backtest_func(params, self.test_start, self.test_end)
            logger.info(f"测试集结果: {result}")
            return result
        except Exception as e:
            logger.error(f"测试集验证失败: {e}")
            return {}
    
    def _calc_overfitting(
        self,
        train_result: Dict,
        test_result: Dict,
        metric: str
    ) -> float:
        """计算过拟合程度
        
        过拟合度 = (训练收益 - 测试收益) / 训练收益
        
        Args:
            train_result: 训练结果
            test_result: 测试结果
            metric: 指标
            
        Returns:
            过拟合度（0最佳，越大越过拟合）
        """
        train_value = train_result.get(metric, 0)
        test_value = test_result.get(metric, 0)
        
        if train_value == 0:
            return 0
        
        return (train_value - test_value) / abs(train_value)
    
    def run_rolling(
        self,
        param_ranges: Dict[str, List],
        backtest_func: Callable,
        window_size: int = 252,  # 交易日
        step_size: int = 63,     # 季度滚动
        metric: str = 'total_return'
    ) -> List[Dict]:
        """滚动Walk-Forward验证
        
        Args:
            param_ranges: 参数范围
            backtest_func: 回测函数
            window_size: 训练窗口大小
            step_size: 滚动步长
            metric: 评估指标
            
        Returns:
            各窗口验证结果
        """
        results = []
        
        # 生成日期序列
        train_start = datetime.strptime(self.train_start, '%Y-%m-%d')
        test_end = datetime.strptime(self.test_end, '%Y-%m-%d')
        
        current_start = train_start
        window_id = 0
        
        while True:
            # 训练期
            train_end = current_start + pd.Timedelta(days=window_size)
            # 测试期
            test_start = train_end + pd.Timedelta(days=1)
            test_end_date = test_start + pd.Timedelta(days=step_size)
            
            if test_end_date > test_end:
                break
            
            logger.info(f"窗口{window_id}: 训练{current_start.date()}-{train_end.date()}, 测试{test_start.date()}-{test_end_date.date()}")
            
            # 优化和验证
            optimal = self._optimize_period(
                param_ranges, backtest_func,
                str(current_start.date()), str(train_end.date()),
                str(test_start.date()), str(test_end_date.date()),
                metric
            )
            
            results.append({
                'window_id': window_id,
                'train_start': str(current_start.date()),
                'train_end': str(train_end.date()),
                'test_start': str(test_start.date()),
                'test_end': str(test_end_date.date()),
                **optimal
            })
            
            current_start = current_start + pd.Timedelta(days=step_size)
            window_id += 1
        
        return results
    
    def _optimize_period(
        self,
        param_ranges, backtest_func,
        train_start, train_end,
        test_start, test_end,
        metric
    ) -> Dict:
        """单期优化"""
        from itertools import product
        
        param_names = list(param_ranges.keys())
        param_values = list(param_ranges.values())
        combinations = list(product(*param_values))
        
        best_params = None
        best_train_score = -np.inf
        test_score = 0
        
        for combo in combinations:
            params = {name: value for name, value in zip(param_names, combo)}
            
            try:
                train_result = backtest_func(params, train_start, train_end)
                train_score = train_result.get(metric, 0)
                
                if train_score > best_train_score:
                    best_train_score = train_score
                    best_params = params
                    test_result = backtest_func(params, test_start, test_end)
                    test_score = test_result.get(metric, 0)
            except:
                pass
        
        return {
            'optimal_params': best_params,
            'train_score': best_train_score,
            'test_score': test_score
        }