# -*- coding: utf-8 -*-
"""Walk-Forward验证"""

from typing import Dict, List, Callable, Any
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from utils.logger import get_logger

logger = get_logger('walk_forward')


class WalkForwardValidator:
    """Walk-Forward验证
    
    滚动窗口验证，避免过拟合
    训练集找最优参数，测试集验证效�?
    """
    
    def __init__(
        self,
        train_window: int = 252 * 3,  # 3年训�?
        test_window: int = 252 * 1,   # 1年测�?
        step: int = 63                 # 滚动步长（季度）
    ):
        self.train_window = train_window
        self.test_window = test_window
        self.step = step
    
    def generate_windows(
        self,
        start_date: str,
        end_date: str,
        trade_dates: List[str] = None
    ) -> List[Dict]:
        """生成滚动窗口
        
        Args:
            start_date: 开始日�?
            end_date: 结束日期
            trade_dates: 交易日列�?
            
        Returns:
            窗口列表 [{'train_start', 'train_end', 'test_start', 'test_end'}, ...]
        """
        if trade_dates is None:
            # 生成简单日期序�?
            dates = pd.date_range(start_date, end_date, freq='B')  # 工作�?
            trade_dates = [d.strftime('%Y-%m-%d') for d in dates]
        
        windows = []
        
        for i in range(0, len(trade_dates) - self.train_window - self.test_window, self.step):
            train_start = trade_dates[i]
            train_end = trade_dates[i + self.train_window - 1]
            test_start = trade_dates[i + self.train_window]
            test_end = trade_dates[min(i + self.train_window + self.test_window - 1, len(trade_dates) - 1)]
            
            windows.append({
                'window_id': len(windows) + 1,
                'train_start': train_start,
                'train_end': train_end,
                'test_start': test_start,
                'test_end': test_end
            })
        
        logger.info(f"生成{len(windows)}个滚动窗�?)
        return windows
    
    def run_validation(
        self,
        optimize_func: Callable,
        validate_func: Callable,
        param_ranges: Dict[str, List],
        start_date: str,
        end_date: str,
        trade_dates: List[str] = None
    ) -> pd.DataFrame:
        """运行Walk-Forward验证
        
        Args:
            optimize_func: 优化函数（训练集找最优参数）
            validate_func: 验证函数（测试集验证效果�?
            param_ranges: 参数范围
            start_date: 开始日�?
            end_date: 结束日期
            trade_dates: 交易日列�?
            
        Returns:
            验证结果
        """
        windows = self.generate_windows(start_date, end_date, trade_dates)
        results = []
        
        for window in windows:
            logger.info(f"窗口 {window['window_id']}: "
                       f"训练 {window['train_start']}~{window['train_end']}, "
                       f"测试 {window['test_start']}~{window['test_end']}")
            
            # 1. 训练集优�?
            optimal_params = optimize_func(
                start_date=window['train_start'],
                end_date=window['train_end'],
                param_ranges=param_ranges
            )
            
            if not optimal_params:
                logger.warning(f"窗口 {window['window_id']} 优化失败")
                continue
            
            # 2. 测试集验�?
            test_metrics = validate_func(
                start_date=window['test_start'],
                end_date=window['test_end'],
                params=optimal_params
            )
            
            # 3. 记录结果
            result = {
                'window_id': window['window_id'],
                'train_start': window['train_start'],
                'train_end': window['train_end'],
                'test_start': window['test_start'],
                'test_end': window['test_end'],
                **optimal_params,
                **test_metrics
            }
            results.append(result)
        
        return pd.DataFrame(results)
    
    def analyze_stability(self, wf_results: pd.DataFrame) -> Dict:
        """分析参数稳定�?
        
        Args:
            wf_results: Walk-Forward结果
            
        Returns:
            稳定性分�?
        """
        if wf_results.empty:
            return {}
        
        # 分析各参数的变化范围
        param_cols = [col for col in wf_results.columns 
                      if col not in ['window_id', 'train_start', 'train_end', 
                                     'test_start', 'test_end', 'sharpe_ratio', 
                                     'total_return', 'max_drawdown', 'win_rate']]
        
        stability = {}
        for col in param_cols:
            values = wf_results[col]
            if values.dtype in ['int64', 'float64']:
                stability[col] = {
                    'mean': values.mean(),
                    'std': values.std(),
                    'cv': values.std() / abs(values.mean()) if values.mean() != 0 else 0,
                    'min': values.min(),
                    'max': values.max()
                }
        
        # 综合评估
        avg_sharpe = wf_results['sharpe_ratio'].mean() if 'sharpe_ratio' in wf_results.columns else 0
        avg_return = wf_results['total_return'].mean() if 'total_return' in wf_results.columns else 0
        
        stability['overall'] = {
            'avg_sharpe': avg_sharpe,
            'avg_return': avg_return,
            'sharpe_stability': wf_results['sharpe_ratio'].std() if 'sharpe_ratio' in wf_results.columns else 0
        }
        
        return stability
    
    def generate_report(self, wf_results: pd.DataFrame) -> str:
        """生成Walk-Forward报告
        
        Args:
            wf_results: 验证结果
            
        Returns:
            文本报告
        """
        stability = self.analyze_stability(wf_results)
        
        lines = [
            "========== Walk-Forward验证报告 ==========",
            "",
            f"窗口数量: {len(wf_results)}",
            "",
            "## 各窗口表�?,
            ""
        ]
        
        for _, row in wf_results.iterrows():
            lines.append(
                f"窗口{row['window_id']}: "
                f"Sharpe={row.get('sharpe_ratio', 0):.2f}, "
                f"收益={row.get('total_return', 0):.2%}"
            )
        
        if 'overall' in stability:
            lines.extend([
                "",
                "## 综合评估",
                "",
                f"平均夏普: {stability['overall']['avg_sharpe']:.2f}",
                f"平均收益: {stability['overall']['avg_return']:.2%}",
                f"夏普稳定�? {stability['overall']['sharpe_stability']:.2f}",
            ])
        
        lines.extend(["", "=========================================="])
        
        return "\n".join(lines)


def train_test_split(
    start_date: str,
    split_date: str,
    end_date: str
) -> tuple:
    """训练测试集划�?
    
    Args:
        start_date: 总开始日�?
        split_date: 划分日期
        end_date: 总结束日�?
        
    Returns:
        (训练集开�? 训练集结�? 测试集开�? 测试集结�?
    """
    return start_date, split_date, split_date, end_date


# 预设划分�?020-2023训练�?024-2025测试
DEFAULT_SPLIT = {
    'train_start': '2020-01-01',
    'train_end': '2023-12-31',
    'test_start': '2024-01-01',
    'test_end': '2025-12-31'
}
