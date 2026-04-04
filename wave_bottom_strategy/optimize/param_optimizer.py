# -*- coding: utf-8 -*-
"""参数优化模块 - 寻找最优参数组�?""

from typing import Dict, List, Any, Tuple
from itertools import product
import pandas as pd
import numpy as np
from datetime import datetime

from backtest.engine import BacktestEngine
from selector.engine import SelectorEngine
from data.loader import DataLoader
from utils.logger import get_logger

logger = get_logger('param_optimizer')


class ParamOptimizer:
    """参数优化�?
    
    通过网格搜索寻找最优参数组�?
    """
    
    def __init__(
        self,
        initial_capital: float = 1_000_000.0,
        train_start: str = '2020-01-01',
        train_end: str = '2023-12-31',
        test_start: str = '2024-01-01',
        test_end: str = '2025-12-31'
    ):
        self.initial_capital = initial_capital
        self.train_start = train_start
        self.train_end = train_end
        self.test_start = test_start
        self.test_end = test_end
        
        self.results: List[Dict] = []
    
    def define_param_grid(self) -> Dict[str, List]:
        """定义参数网格
        
        Returns:
            参数网格定义
        """
        return {
            # KDJ参数
            'kdj_n': [9, 14],
            'kdj_m1': [3],
            'kdj_m2': [3],
            
            # 选股参数
            'min_score': [60, 70, 80],
            'max_positions': [5, 10],
            'single_position_pct': [0.08, 0.10],
            
            # 回测参数
            'rebalance_freq': [5, 10, 20],
        }
    
    def grid_search(
        self,
        param_grid: Dict[str, List] = None,
        stock_pool: List[str] = None,
        max_combinations: int = 50
    ) -> pd.DataFrame:
        """网格搜索
        
        Args:
            param_grid: 参数网格
            stock_pool: 股票�?
            max_combinations: 最大组合数
            
        Returns:
            优化结果
        """
        if param_grid is None:
            param_grid = self.define_param_grid()
        
        # 生成所有参数组�?
        keys = param_grid.keys()
        values = param_grid.values()
        combinations = list(product(*values))
        
        logger.info(f"参数组合�? {len(combinations)}")
        
        # 限制组合�?
        if len(combinations) > max_combinations:
            logger.warning(f"组合数超过{max_combinations}，随机采�?)
            import random
            combinations = random.sample(combinations, max_combinations)
        
        results = []
        
        for i, combo in enumerate(combinations):
            params = dict(zip(keys, combo))
            logger.info(f"测试组合 {i+1}/{len(combinations)}: {params}")
            
            try:
                # 运行回测
                result = self._run_backtest(params, stock_pool)
                
                if result and 'error' not in result:
                    results.append({
                        **params,
                        'total_return': result.get('total_return', 0),
                        'annual_return': result.get('annual_return', 0),
                        'max_drawdown': result.get('max_drawdown', 0),
                        'sharpe_ratio': result.get('sharpe_ratio', 0),
                        'win_rate': result.get('win_rate', 0),
                        'trade_count': result.get('trade_count', 0)
                    })
            except Exception as e:
                logger.warning(f"组合测试失败: {e}")
        
        self.results = results
        return pd.DataFrame(results)
    
    def _run_backtest(
        self,
        params: Dict[str, Any],
        stock_pool: List[str] = None
    ) -> Dict:
        """运行单次回测"""
        # 创建回测引擎
        engine = BacktestEngine(
            initial_capital=self.initial_capital,
            max_positions=params.get('max_positions', 10),
            single_position_pct=params.get('single_position_pct', 0.10)
        )
        
        # 运行回测
        result = engine.run(
            start_date=self.train_start,
            end_date=self.train_end,
            stock_pool=stock_pool,
            rebalance_freq=params.get('rebalance_freq', 5)
        )
        
        return result
    
    def walk_forward_validation(
        self,
        window_size: int = 252,  # 1�?
        step_size: int = 63      # 3个月
    ) -> pd.DataFrame:
        """Walk-Forward验证
        
        Args:
            window_size: 训练窗口大小（天�?
            step_size: 步进大小（天�?
            
        Returns:
            验证结果
        """
        logger.info("开始Walk-Forward验证...")
        
        # 生成训练/测试窗口
        start = datetime.strptime(self.train_start, '%Y-%m-%d')
        end = datetime.strptime(self.test_end, '%Y-%m-%d')
        
        results = []
        current = start
        
        while current < end:
            train_end = min(
                current + pd.Timedelta(days=window_size),
                end
            )
            test_end = min(
                train_end + pd.Timedelta(days=step_size),
                end
            )
            
            logger.info(f"窗口: {current.date()} - {test_end.date()}")
            
            # TODO: 在训练窗口优化参数，在测试窗口验�?
            
            current = train_end + pd.Timedelta(days=1)
        
        return pd.DataFrame(results)
    
    def find_optimal_params(
        self,
        metric: str = 'sharpe_ratio',
        top_n: int = 5
    ) -> pd.DataFrame:
        """找出最优参�?
        
        Args:
            metric: 优化指标
            top_n: 返回前N�?
            
        Returns:
            最优参数组�?
        """
        if not self.results:
            logger.error("无优化结果，请先运行grid_search")
            return pd.DataFrame()
        
        df = pd.DataFrame(self.results)
        
        # 按指标排�?
        sorted_df = df.sort_values(metric, ascending=False)
        
        return sorted_df.head(top_n)
    
    def generate_report(self) -> str:
        """生成优化报告"""
        if not self.results:
            return "无优化结�?
        
        df = pd.DataFrame(self.results)
        
        optimal = self.find_optimal_params()
        
        report = f"""# 参数优化报告

## 优化设置
- 训练�? {self.train_start} ~ {self.train_end}
- 测试�? {self.test_start} ~ {self.test_end}
- 组合�? {len(self.results)}

## 最优参数组合（按夏普比率）

{optimal.to_markdown()}

## 统计摘要

| 指标 | 均�?| 最�?| 最�?|
|------|------|------|------|
| 总收益率 | {df['total_return'].mean():.2%} | {df['total_return'].max():.2%} | {df['total_return'].min():.2%} |
| 夏普比率 | {df['sharpe_ratio'].mean():.2f} | {df['sharpe_ratio'].max():.2f} | {df['sharpe_ratio'].min():.2f} |
| 最大回�?| {df['max_drawdown'].mean():.2%} | {df['max_drawdown'].max():.2%} | {df['max_drawdown'].min():.2%} |
"""
        
        return report


def run_optimization():
    """运行参数优化"""
    optimizer = ParamOptimizer()
    
    # 网格搜索
    results = optimizer.grid_search(max_combinations=20)
    
    # 找最优参�?
    optimal = optimizer.find_optimal_params()
    
    print("\n最优参数组�?")
    print(optimal)
    
    # 生成报告
    report = optimizer.generate_report()
    
    # 保存报告
    report_path = Path('docs/参数优化报告.md')
    report_path.write_text(report, encoding='utf-8')
    print(f"\n报告已保�? {report_path}")
    
    return optimal


if __name__ == '__main__':
    run_optimization()
