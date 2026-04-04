# -*- coding: utf-8 -*-
"""参数优化�?- 整合优化流程"""

from typing import Dict, List, Callable, Any
import pandas as pd
import numpy as np
from pathlib import Path

from .sensitivity import SensitivityAnalysis, default_param_ranges
from .walk_forward import WalkForwardValidator, DEFAULT_SPLIT
from .metrics import PerformanceMetrics
from utils.logger import get_logger

logger = get_logger('parameter_optimizer')


class ParameterOptimizer:
    """参数优化�?
    
    整合敏感性分析、网格搜索、Walk-Forward验证
    """
    
    def __init__(self, backtest_func: Callable):
        """
        Args:
            backtest_func: 回测函数，接�?start_date, end_date, params)返回指标字典
        """
        self.backtest_func = backtest_func
        self.results = {}
    
    def sensitivity_analysis(
        self,
        param_ranges: Dict[str, List] = None,
        start_date: str = DEFAULT_SPLIT['train_start'],
        end_date: str = DEFAULT_SPLIT['train_end']
    ) -> pd.DataFrame:
        """单参数敏感性分�?
        
        Args:
            param_ranges: 参数范围
            start_date: 开始日�?
            end_date: 结束日期
            
        Returns:
            敏感性分析结�?
        """
        if param_ranges is None:
            param_ranges = default_param_ranges()
        
        logger.info(f"敏感性分�? {start_date} ~ {end_date}")
        
        results = []
        
        for param_name, param_values in param_ranges.items():
            logger.info(f"分析参数: {param_name}")
            
            for value in param_values:
                # 固定其他参数，只变化当前参数
                params = self._get_default_params()
                params[param_name] = value
                
                try:
                    metrics = self.backtest_func(start_date, end_date, params)
                    results.append({
                        'param_name': param_name,
                        'param_value': value,
                        **metrics
                    })
                except Exception as e:
                    logger.warning(f"参数 {param_name}={value} 失败: {e}")
        
        df = pd.DataFrame(results)
        self.results['sensitivity'] = df
        
        return df
    
    def grid_search(
        self,
        param_ranges: Dict[str, List],
        start_date: str = DEFAULT_SPLIT['train_start'],
        end_date: str = DEFAULT_SPLIT['train_end'],
        metric: str = 'sharpe_ratio'
    ) -> tuple:
        """多参数网格搜�?
        
        Args:
            param_ranges: 参数网格
            start_date: 开始日�?
            end_date: 结束日期
            metric: 优化指标
            
        Returns:
            (最优参�? 最优指�? 全部结果)
        """
        logger.info(f"网格搜索: {len(self._generate_combinations(param_ranges))}�?)
        
        sa = SensitivityAnalysis(param_ranges)
        results = sa.run_analysis(
            lambda p: self.backtest_func(start_date, end_date, p)
        )
        
        optimal = sa.find_optimal(results, metric)
        
        self.results['grid_search'] = results
        
        return optimal, results
    
    def walk_forward_validation(
        self,
        param_ranges: Dict[str, List],
        start_date: str = '2020-01-01',
        end_date: str = '2025-12-31',
        optimize_metric: str = 'sharpe_ratio'
    ) -> pd.DataFrame:
        """Walk-Forward验证
        
        Args:
            param_ranges: 参数范围
            start_date: 总开始日�?
            end_date: 总结束日�?
            optimize_metric: 优化指标
            
        Returns:
            Walk-Forward结果
        """
        logger.info("开始Walk-Forward验证")
        
        wf = WalkForwardValidator()
        
        def optimize_func(start, end, param_ranges):
            result, _ = self.grid_search(param_ranges, start, end, optimize_metric)
            return result
        
        def validate_func(start, end, params):
            return self.backtest_func(start, end, params)
        
        results = wf.run_validation(
            optimize_func=optimize_func,
            validate_func=validate_func,
            param_ranges=param_ranges,
            start_date=start_date,
            end_date=end_date
        )
        
        self.results['walk_forward'] = results
        
        return results
    
    def train_test_validate(
        self,
        optimal_params: Dict,
        train_start: str = DEFAULT_SPLIT['train_start'],
        train_end: str = DEFAULT_SPLIT['train_end'],
        test_start: str = DEFAULT_SPLIT['test_start'],
        test_end: str = DEFAULT_SPLIT['test_end']
    ) -> Dict:
        """训练集测试集验证
        
        Args:
            optimal_params: 最优参�?
            train_start/end: 训练集范�?
            test_start/end: 测试集范�?
            
        Returns:
            验证结果
        """
        logger.info(f"训练集验�? {train_start} ~ {train_end}")
        train_metrics = self.backtest_func(train_start, train_end, optimal_params)
        
        logger.info(f"测试集验�? {test_start} ~ {test_end}")
        test_metrics = self.backtest_func(test_start, test_end, optimal_params)
        
        result = {
            'train': train_metrics,
            'test': test_metrics,
            'overfit_score': self._calc_overfit_score(train_metrics, test_metrics)
        }
        
        self.results['train_test'] = result
        
        return result
    
    def _get_default_params(self) -> Dict:
        """获取默认参数"""
        return {
            'min_score': 70,
            'kdj_threshold': 20,
            'stop_loss': -0.05,
            'take_profit': 0.15,
            'max_hold_days': 5,
            'position_size': 0.1
        }
    
    def _generate_combinations(self, param_ranges: Dict) -> List[Dict]:
        """生成参数组合"""
        from itertools import product
        keys = list(param_ranges.keys())
        values = list(param_ranges.values())
        return [dict(zip(keys, combo)) for combo in product(*values)]
    
    def _calc_overfit_score(self, train_metrics: Dict, test_metrics: Dict) -> float:
        """计算过拟合分�?
        
        过拟合分�?= 训练集夏�?/ 测试集夏�?
        接近1表示不过拟合
        """
        train_sharpe = train_metrics.get('sharpe_ratio', 0)
        test_sharpe = test_metrics.get('sharpe_ratio', 0)
        
        if test_sharpe == 0:
            return float('inf') if train_sharpe > 0 else 0
        
        return train_sharpe / test_sharpe
    
    def generate_optimization_report(self) -> str:
        """生成优化报告"""
        lines = [
            "========== 参数优化报告 ==========",
            ""
        ]
        
        # 敏感性分�?
        if 'sensitivity' in self.results:
            sens = self.results['sensitivity']
            lines.extend([
                "## 敏感性分�?,
                f"测试参数组合�? {len(sens)}",
                ""
            ])
            
            # 各参数影�?
            for param in sens['param_name'].unique():
                param_data = sens[sens['param_name'] == param]
                best_row = param_data.loc[param_data['sharpe_ratio'].idxmax()]
                lines.append(
                    f"  {param}: 最优�?{best_row['param_value']}, "
                    f"Sharpe={best_row['sharpe_ratio']:.2f}"
                )
            
            lines.append("")
        
        # 网格搜索
        if 'grid_search' in self.results:
            grid = self.results['grid_search']
            best = grid.loc[grid['sharpe_ratio'].idxmax()]
            lines.extend([
                "## 网格搜索",
                f"最优参数组�?",
                f"  Sharpe: {best['sharpe_ratio']:.2f}",
                f"  收益: {best.get('total_return', 0):.2%}",
                ""
            ])
        
        # Walk-Forward
        if 'walk_forward' in self.results:
            wf = self.results['walk_forward']
            lines.extend([
                "## Walk-Forward验证",
                f"窗口�? {len(wf)}",
                f"平均Sharpe: {wf['sharpe_ratio'].mean():.2f}",
                f"Sharpe稳定�? {wf['sharpe_ratio'].std():.2f}",
                ""
            ])
        
        # 训练测试验证
        if 'train_test' in self.results:
            tt = self.results['train_test']
            lines.extend([
                "## 训练/测试验证",
                f"训练集Sharpe: {tt['train'].get('sharpe_ratio', 0):.2f}",
                f"测试集Sharpe: {tt['test'].get('sharpe_ratio', 0):.2f}",
                f"过拟合分�? {tt['overfit_score']:.2f} (越接�?越好)",
                ""
            ])
        
        lines.append("==================================")
        
        return "\n".join(lines)


# 预设参数范围
STOP_LOSS_RANGE = [-0.03, -0.05, -0.07, -0.10]
TAKE_PROFIT_RANGE = [0.10, 0.15, 0.20, 0.25]
HOLD_DAYS_RANGE = [3, 5, 7, 10, 15]
POSITION_SIZE_RANGE = [0.05, 0.10, 0.15, 0.20]
MIN_SCORE_RANGE = [50, 60, 70, 80]
KDJ_THRESHOLD_RANGE = [10, 15, 20, 25]
