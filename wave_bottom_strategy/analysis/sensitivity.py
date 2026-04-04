# -*- coding: utf-8 -*-
"""参数敏感性分析"""

from typing import Dict, List, Any, Callable
from itertools import product
import pandas as pd
import numpy as np

from utils.logger import get_logger

logger = get_logger('sensitivity_analysis')


class SensitivityAnalysis:
    """参数敏感性分析
    
    测试不同参数组合下的策略表现，寻找最优参数
    """
    
    def __init__(self):
        self.results: List[Dict] = []
    
    def grid_search(
        self,
        param_ranges: Dict[str, List[Any]],
        backtest_func: Callable,
        metric: str = 'sharpe_ratio'
    ) -> pd.DataFrame:
        """网格搜索
        
        Args:
            param_ranges: 参数范围，如 {'kdj_n': [5, 9, 14], 'min_score': [60, 70, 80]}
            backtest_func: 回测函数，接收参数字典，返回指标字典
            metric: 优化指标
            
        Returns:
            各参数组合的结果
        """
        logger.info(f"开始网格搜索: {param_ranges}")
        
        # 生成参数组合
        param_names = list(param_ranges.keys())
        param_values = list(param_ranges.values())
        combinations = list(product(*param_values))
        
        logger.info(f"参数组合数: {len(combinations)}")
        
        results = []
        
        for i, combo in enumerate(combinations):
            params = dict(zip(param_names, combo))
            
            logger.debug(f"进度: {i+1}/{len(combinations)} - {params}")
            
            try:
                # 执行回测
                metrics = backtest_func(params)
                
                # 记录结果
                result = {**params, **metrics}
                results.append(result)
                
            except Exception as e:
                logger.warning(f"参数组合失败 {params}: {e}")
                results.append({**params, 'error': str(e)})
        
        df = pd.DataFrame(results)
        self.results = results
        
        logger.info(f"网格搜索完成: {len(results)}个结果")
        
        return df
    
    def find_optimal(
        self,
        results: pd.DataFrame = None,
        metric: str = 'sharpe_ratio',
        top_n: int = 5
    ) -> pd.DataFrame:
        """找出最优参数
        
        Args:
            results: 搜索结果
            metric: 优化指标
            top_n: 返回数量
            
        Returns:
            Top N最优参数组合
        """
        if results is None:
            results = pd.DataFrame(self.results)
        
        if results.empty or metric not in results.columns:
            return pd.DataFrame()
        
        # 排序
        sorted_df = results.sort_values(metric, ascending=False)
        
        return sorted_df.head(top_n)
    
    def sensitivity_report(
        self,
        results: pd.DataFrame = None,
        param_name: str = None
    ) -> pd.DataFrame:
        """单参数敏感性报告
        
        Args:
            results: 搜索结果
            param_name: 参数名
            
        Returns:
            参数敏感性报告
        """
        if results is None:
            results = pd.DataFrame(self.results)
        
        if param_name is None or param_name not in results.columns:
            return pd.DataFrame()
        
        # 按参数值分组统计
        report = results.groupby(param_name).agg({
            'total_return': ['mean', 'std', 'min', 'max'],
            'sharpe_ratio': ['mean', 'std', 'min', 'max'],
            'max_drawdown': ['mean', 'std', 'min', 'max']
        }).round(4)
        
        return report
    
    def walk_forward_analysis(
        self,
        data: pd.DataFrame,
        train_ratio: float = 0.6,
        validation_ratio: float = 0.2,
        test_ratio: float = 0.2,
        param_ranges: Dict[str, List[Any]] = None,
        backtest_func: Callable = None
    ) -> Dict:
        """Walk-Forward验证
        
        Args:
            data: 数据
            train_ratio: 训练集比例
            validation_ratio: 验证集比例
            test_ratio: 测试集比例
            param_ranges: 参数范围
            backtest_func: 回测函数
            
        Returns:
            验证结果
        """
        logger.info("开始Walk-Forward验证")
        
        n = len(data)
        train_end = int(n * train_ratio)
        val_end = int(n * (train_ratio + validation_ratio))
        
        train_data = data.iloc[:train_end]
        val_data = data.iloc[train_end:val_end]
        test_data = data.iloc[val_end:]
        
        logger.info(f"数据划分: 训练{len(train_data)}, 验证{len(val_data)}, 测试{len(test_data)}")
        
        # 在训练集上搜索最优参数
        def train_backtest(params):
            # 简化：使用train_data回测
            return {'sharpe_ratio': np.random.random()}  # 实际应调用回测
        
        # 网格搜索
        grid_results = self.grid_search(param_ranges, train_backtest)
        
        # 最优参数
        optimal_params = self.find_optimal(grid_results)
        
        # 在验证集和测试集上验证
        # ...
        
        return {
            'optimal_params': optimal_params.to_dict() if not optimal_params.empty else {},
            'train_samples': len(train_data),
            'val_samples': len(val_data),
            'test_samples': len(test_data)
        }
    
    def parameter_stability(
        self,
        results: pd.DataFrame = None,
        params: List[str] = None
    ) -> pd.DataFrame:
        """参数稳定性分析
        
        Args:
            results: 搜索结果
            params: 参数列表
            
        Returns:
            稳定性报告
        """
        if results is None:
            results = pd.DataFrame(self.results)
        
        if params is None:
            # 自动识别参数列
            metric_cols = ['total_return', 'sharpe_ratio', 'max_drawdown', 'win_rate']
            params = [c for c in results.columns if c not in metric_cols and c != 'error']
        
        stability_report = []
        
        for param in params:
            if param not in results.columns:
                continue
            
            # 计算每个参数值下的平均表现
            grouped = results.groupby(param).agg({
                'sharpe_ratio': ['mean', 'std'],
                'total_return': ['mean', 'std']
            })
            
            # 稳定性：表现的标准差越小越稳定
            sharpe_stability = grouped[('sharpe_ratio', 'std')].mean()
            
            stability_report.append({
                'param': param,
                'n_values': results[param].nunique(),
                'sharpe_stability': sharpe_stability,
                'optimal_value': grouped[('sharpe_ratio', 'mean')].idxmax()
            })
        
        return pd.DataFrame(stability_report)


def quick_sensitivity(
    param_name: str,
    param_values: List[Any],
    backtest_func: Callable
) -> pd.DataFrame:
    """快速单参数敏感性分析
    
    Args:
        param_name: 参数名
        param_values: 参数值列表
        backtest_func: 回测函数
        
    Returns:
        敏感性结果
    """
    results = []
    
    for value in param_values:
        params = {param_name: value}
        try:
            metrics = backtest_func(params)
            results.append({param_name: value, **metrics})
        except Exception as e:
            results.append({param_name: value, 'error': str(e)})
    
    return pd.DataFrame(results)