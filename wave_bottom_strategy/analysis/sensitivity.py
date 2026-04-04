# -*- coding: utf-8 -*-
"""参数敏感性分析"""

from typing import Dict, List, Any, Callable
from itertools import product
import pandas as pd
import numpy as np

from utils.logger import get_logger

logger = get_logger('sensitivity')


class SensitivityAnalysis:
    """参数敏感性分析
    
    测试单个参数变化对策略表现的影响
    """
    
    def __init__(self, base_params: Dict[str, Any]):
        """初始化
        
        Args:
            base_params: 基础参数配置
        """
        self.base_params = base_params
        self.results: List[Dict] = []
    
    def analyze_single_param(
        self,
        param_name: str,
        param_range: List[Any],
        backtest_func: Callable,
        metric: str = 'total_return'
    ) -> pd.DataFrame:
        """单参数敏感性分析
        
        Args:
            param_name: 参数名
            param_range: 参数取值范围
            backtest_func: 回测函数
            metric: 评估指标
            
        Returns:
            敏感性分析结果
        """
        logger.info(f"单参数敏感性分析: {param_name}, 范围: {param_range}")
        
        results = []
        
        for value in param_range:
            # 构建参数
            params = {**self.base_params, param_name: value}
            
            try:
                # 执行回测
                backtest_result = backtest_func(params)
                
                results.append({
                    'param_name': param_name,
                    'param_value': value,
                    'metric': backtest_result.get(metric, 0),
                    'total_return': backtest_result.get('total_return', 0),
                    'max_drawdown': backtest_result.get('max_drawdown', 0),
                    'sharpe': backtest_result.get('sharpe', 0),
                    'win_rate': backtest_result.get('win_rate', 0),
                })
                
            except Exception as e:
                logger.warning(f"参数 {param_name}={value} 回测失败: {e}")
                results.append({
                    'param_name': param_name,
                    'param_value': value,
                    'metric': 0,
                    'error': str(e)
                })
        
        df = pd.DataFrame(results)
        
        # 分析敏感性
        self._analyze_sensitivity(df, param_name, metric)
        
        return df
    
    def _analyze_sensitivity(self, df: pd.DataFrame, param_name: str, metric: str):
        """分析敏感性
        
        Args:
            df: 结果DataFrame
            param_name: 参数名
            metric: 指标名
        """
        if df.empty:
            return
        
        valid_df = df[df['metric'] != 0]
        
        if valid_df.empty:
            logger.warning(f"{param_name}: 无有效结果")
            return
        
        # 计算指标变异系数
        cv = valid_df['metric'].std() / valid_df['metric'].mean() if valid_df['metric'].mean() != 0 else 0
        
        # 找最优值
        best_row = valid_df.loc[valid_df['metric'].idxmax()]
        
        logger.info(f"{param_name} 敏感性分析:")
        logger.info(f"  - 变异系数: {cv:.4f}")
        logger.info(f"  - 最优值: {best_row['param_value']}")
        logger.info(f"  - 最优{metric}: {best_row['metric']:.4f}")
    
    def find_sensitive_params(self, threshold: float = 0.1) -> List[str]:
        """找出敏感参数
        
        Args:
            threshold: 变异系数阈值
            
        Returns:
            敏感参数列表
        """
        # TODO: 基于历史分析结果判断
        return []


class GridSearch:
    """多参数网格搜索
    
    遍历参数组合，找出最优参数
    """
    
    def __init__(
        self,
        param_grid: Dict[str, List[Any]],
        backtest_func: Callable
    ):
        """初始化
        
        Args:
            param_grid: 参数网格 {参数名: 取值列表}
            backtest_func: 回测函数
        """
        self.param_grid = param_grid
        self.backtest_func = backtest_func
        self.results: List[Dict] = []
    
    def run(self, metric: str = 'sharpe') -> pd.DataFrame:
        """执行网格搜索
        
        Args:
            metric: 优化指标
            
        Returns:
            搜索结果
        """
        # 生成参数组合
        param_names = list(self.param_grid.keys())
        param_values = list(self.param_grid.values())
        combinations = list(product(*param_values))
        
        total = len(combinations)
        logger.info(f"网格搜索: {total} 组参数")
        
        for i, combo in enumerate(combinations):
            params = dict(zip(param_names, combo))
            
            logger.info(f"进度: {i+1}/{total} - {params}")
            
            try:
                result = self.backtest_func(params)
                
                self.results.append({
                    **params,
                    'total_return': result.get('total_return', 0),
                    'max_drawdown': result.get('max_drawdown', 0),
                    'sharpe': result.get('sharpe', 0),
                    'win_rate': result.get('win_rate', 0),
                    'profit_loss_ratio': result.get('profit_loss_ratio', 0),
                })
                
            except Exception as e:
                logger.warning(f"参数组合失败: {params}, {e}")
        
        return pd.DataFrame(self.results)
    
    def get_best_params(self, metric: str = 'sharpe') -> Dict:
        """获取最优参数
        
        Args:
            metric: 优化指标
            
        Returns:
            最优参数
        """
        if not self.results:
            return {}
        
        df = pd.DataFrame(self.results)
        
        if df.empty or metric not in df.columns:
            return {}
        
        best_idx = df[metric].idxmax()
        best_row = df.loc[best_idx]
        
        # 提取参数
        param_names = list(self.param_grid.keys())
        best_params = {k: best_row[k] for k in param_names}
        
        logger.info(f"最优参数: {best_params}")
        logger.info(f"最优{metric}: {best_row[metric]:.4f}")
        
        return best_params
    
    def get_top_n_params(self, n: int = 5, metric: str = 'sharpe') -> pd.DataFrame:
        """获取Top N参数组合
        
        Args:
            n: 数量
            metric: 指标
            
        Returns:
            Top N结果
        """
        df = pd.DataFrame(self.results)
        
        if df.empty:
            return df
        
        return df.nlargest(n, metric)


class WalkForwardValidation:
    """Walk-Forward验证
    
    样本内训练，样本外测试
    """
    
    def __init__(
        self,
        train_start: str,
        train_end: str,
        test_start: str,
        test_end: str
    ):
        """初始化
        
        Args:
            train_start: 训练集开始
            train_end: 训练集结束
            test_start: 测试集开始
            test_end: 测试集结束
        """
        self.train_start = train_start
        self.train_end = train_end
        self.test_start = test_start
        self.test_end = test_end
    
    def validate(
        self,
        param_grid: Dict[str, List[Any]],
        train_func: Callable,
        test_func: Callable,
        metric: str = 'sharpe'
    ) -> Dict:
        """执行验证
        
        Args:
            param_grid: 参数网格
            train_func: 训练函数（在训练集上网格搜索）
            test_func: 测试函数（在测试集上验证）
            metric: 优化指标
            
        Returns:
            验证结果
        """
        logger.info(f"Walk-Forward验证:")
        logger.info(f"  训练集: {self.train_start} - {self.train_end}")
        logger.info(f"  测试集: {self.test_start} - {self.test_end}")
        
        # Step 1: 训练集上网格搜索
        logger.info("Step 1: 训练集优化...")
        grid_search = GridSearch(param_grid, train_func)
        train_results = grid_search.run(metric)
        best_params = grid_search.get_best_params(metric)
        
        logger.info(f"训练集最优参数: {best_params}")
        
        # Step 2: 测试集验证
        logger.info("Step 2: 测试集验证...")
        test_result = test_func(best_params)
        
        logger.info(f"测试集结果: {test_result}")
        
        # Step 3: 对比分析
        train_best_result = train_results.loc[train_results[metric].idxmax()]
        
        result = {
            'best_params': best_params,
            'train_metric': train_best_result.get(metric, 0),
            'test_metric': test_result.get(metric, 0),
            'train_return': train_best_result.get('total_return', 0),
            'test_return': test_result.get('total_return', 0),
            'train_drawdown': train_best_result.get('max_drawdown', 0),
            'test_drawdown': test_result.get('max_drawdown', 0),
            'degradation': 0  # 指标衰减
        }
        
        # 计算衰减
        if result['train_metric'] != 0:
            result['degradation'] = (result['train_metric'] - result['test_metric']) / abs(result['train_metric'])
        
        logger.info(f"指标衰减: {result['degradation']:.2%}")
        
        return result
    
    def validate_stability(
        self,
        param_grid: Dict[str, List[Any]],
        train_func: Callable,
        test_func: Callable,
        metric: str = 'sharpe',
        stability_threshold: float = 0.3
    ) -> Dict:
        """验证参数稳定性
        
        Args:
            param_grid: 参数网格
            train_func: 训练函数
            test_func: 测试函数
            metric: 指标
            stability_threshold: 稳定性阈值
            
        Returns:
            稳定性分析结果
        """
        result = self.validate(param_grid, train_func, test_func, metric)
        
        is_stable = result['degradation'] < stability_threshold
        
        result['is_stable'] = is_stable
        result['stability_threshold'] = stability_threshold
        
        if is_stable:
            logger.info(f"✅ 参数稳定，衰减 {result['degradation']:.2%} < {stability_threshold:.2%}")
        else:
            logger.warning(f"⚠️ 参数不稳定，衰减 {result['degradation']:.2%} >= {stability_threshold:.2%}")
        
        return result