# -*- coding: utf-8 -*-
"""Walk-Forward验证"""

from typing import Dict, List, Any, Callable, Tuple
import pandas as pd
import numpy as np
from datetime import datetime

from utils.logger import get_logger

logger = get_logger('walk_forward')


class WalkForwardValidator:
    """Walk-Forward验证
    
    样本内外验证，防止过拟合
    
    流程：
    1. 训练期找最优参数
    2. 测试期验证效果
    3. 滚动窗口重复
    """
    
    def __init__(
        self,
        train_period: int = 3,    # 训练期（年）
        test_period: int = 1,      # 测试期（年）
        step: int = 1              # 步长（年）
    ):
        """初始化
        
        Args:
            train_period: 训练期长度
            test_period: 测试期长度
            step: 滚动步长
        """
        self.train_period = train_period
        self.test_period = test_period
        self.step = step
        self.results: List[Dict] = []
    
    def run(
        self,
        start_year: int,
        end_year: int,
        optimize_func: Callable,
        backtest_func: Callable
    ) -> pd.DataFrame:
        """执行Walk-Forward验证
        
        Args:
            start_year: 开始年份
            end_year: 结束年份
            optimize_func: 参数优化函数
            backtest_func: 回测函数
            
        Returns:
            验证结果
        """
        logger.info(f"Walk-Forward验证: {start_year}-{end_year}")
        
        results = []
        
        # 滚动窗口
        current_start = start_year
        
        while current_start + self.train_period <= end_year:
            train_start = current_start
            train_end = current_start + self.train_period - 1
            test_start = train_end + 1
            test_end = min(test_start + self.test_period - 1, end_year)
            
            logger.info(f"训练: {train_start}-{train_end}, 测试: {test_start}-{test_end}")
            
            # 训练期优化参数
            train_params = optimize_func(train_start, train_end)
            
            # 测试期验证
            test_result = backtest_func(test_start, test_end, train_params)
            
            results.append({
                'train_period': f"{train_start}-{train_end}",
                'test_period': f"{test_start}-{test_end}",
                'optimal_params': train_params,
                'test_return': test_result.get('total_return', 0),
                'test_sharpe': test_result.get('sharpe', 0),
                'test_max_dd': test_result.get('max_drawdown', 0)
            })
            
            # 滚动
            current_start += self.step
            
            if test_end >= end_year:
                break
        
        self.results = results
        return pd.DataFrame(results)
    
    def get_statistics(self) -> Dict:
        """获取统计结果
        
        Returns:
            统计信息
        """
        if not self.results:
            return {}
        
        df = pd.DataFrame(self.results)
        
        # 测试期平均表现
        avg_return = df['test_return'].mean()
        avg_sharpe = df['test_sharpe'].mean()
        avg_max_dd = df['test_max_dd'].mean()
        
        # 胜率（正收益比例）
        win_rate = (df['test_return'] > 0).mean()
        
        return {
            'avg_return': avg_return,
            'avg_sharpe': avg_sharpe,
            'avg_max_drawdown': avg_max_dd,
            'win_rate': win_rate,
            'periods': len(df)
        }
    
    def is_overfitting(
        self,
        train_returns: List[float],
        test_returns: List[float],
        threshold: float = 0.5
    ) -> bool:
        """判断是否过拟合
        
        Args:
            train_returns: 训练期收益
            test_returns: 测试期收益
            threshold: 阈值
            
        Returns:
            是否过拟合
        """
        if not train_returns or not test_returns:
            return False
        
        avg_train = np.mean(train_returns)
        avg_test = np.mean(test_returns)
        
        # 测试期收益远低于训练期
        if avg_train > 0 and avg_test < avg_train * threshold:
            return True
        
        return False


class RollingOptimizer:
    """滚动优化器
    
    定期重新优化参数
    """
    
    def __init__(
        self,
        rebalance_months: int = 3,
        lookback_months: int = 12
    ):
        """初始化
        
        Args:
            rebalance_months: 再平衡周期（月）
            lookback_months: 回看期（月）
        """
        self.rebalance_months = rebalance_months
        self.lookback_months = lookback_months
    
    def get_optimization_schedule(
        self,
        start_date: str,
        end_date: str
    ) -> List[Tuple[str, str, str]]:
        """获取优化时间表
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            [(优化日期, 训练开始, 训练结束), ...]
        """
        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')
        
        schedule = []
        current = start
        
        while current <= end:
            # 训练期
            train_end = current
            train_start_month = current.month - self.lookback_months
            train_start_year = current.year
            
            while train_start_month <= 0:
                train_start_month += 12
                train_start_year -= 1
            
            train_start = datetime(train_start_year, train_start_month, 1)
            
            schedule.append((
                current.strftime('%Y-%m-%d'),
                train_start.strftime('%Y-%m-%d'),
                train_end.strftime('%Y-%m-%d')
            ))
            
            # 下一个优化点
            month = current.month + self.rebalance_months
            year = current.year
            
            while month > 12:
                month -= 12
                year += 1
            
            current = datetime(year, month, 1)
        
        return schedule


class CrossValidator:
    """交叉验证
    
    K折交叉验证用于参数优化
    """
    
    def __init__(self, n_folds: int = 5):
        """初始化
        
        Args:
            n_folds: 折数
        """
        self.n_folds = n_folds
    
    def split(
        self,
        dates: pd.DatetimeIndex
    ) -> List[Tuple[pd.DatetimeIndex, pd.DatetimeIndex]]:
        """生成训练测试分割
        
        Args:
            dates: 日期索引
            
        Returns:
            [(train_idx, test_idx), ...]
        """
        n = len(dates)
        fold_size = n // self.n_folds
        
        splits = []
        
        for i in range(self.n_folds):
            test_start = i * fold_size
            test_end = test_start + fold_size if i < self.n_folds - 1 else n
            
            test_idx = dates[test_start:test_end]
            train_idx = dates[~dates.isin(test_idx)]
            
            splits.append((train_idx, test_idx))
        
        return splits
    
    def validate(
        self,
        data: pd.DataFrame,
        optimize_func: Callable,
        backtest_func: Callable
    ) -> Dict:
        """执行交叉验证
        
        Args:
            data: 数据
            optimize_func: 优化函数
            backtest_func: 回测函数
            
        Returns:
            验证结果
        """
        dates = data['trade_date'].unique()
        
        fold_results = []
        
        for i, (train_idx, test_idx) in enumerate(self.split(dates)):
            logger.info(f"Fold {i+1}/{self.n_folds}")
            
            # 训练
            params = optimize_func(data[data['trade_date'].isin(train_idx)])
            
            # 测试
            result = backtest_func(data[data['trade_date'].isin(test_idx)], params)
            
            fold_results.append(result)
        
        # 汇总
        avg_return = np.mean([r.get('total_return', 0) for r in fold_results])
        std_return = np.std([r.get('total_return', 0) for r in fold_results])
        
        return {
            'avg_return': avg_return,
            'std_return': std_return,
            'fold_results': fold_results
        }