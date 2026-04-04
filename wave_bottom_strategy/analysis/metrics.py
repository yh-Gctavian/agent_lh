# -*- coding: utf-8 -*-
"""绩效指标计算"""

from typing import Dict
import pandas as pd
import numpy as np

from wave_bottom_strategy.utils.logger import get_logger

logger = get_logger('performance_metrics')


class PerformanceMetrics:
    """绩效指标计算
    
    计算胜率、盈亏比、夏普比率等核心指标
    """
    
    def __init__(self, returns: pd.Series = None, trades: pd.DataFrame = None):
        self.returns = returns
        self.trades = trades
    
    def win_rate(self) -> float:
        """计算胜率
        
        Returns:
            胜率（盈利交易占比）
        """
        if self.trades is None or self.trades.empty:
            return 0.0
        
        # 从交易记录计算
        if 'profit' in self.trades.columns:
            winning = len(self.trades[self.trades['profit'] > 0])
            total = len(self.trades[self.trades['profit'] != 0])
        elif 'return' in self.trades.columns:
            winning = len(self.trades[self.trades['return'] > 0])
            total = len(self.trades[self.trades['return'] != 0])
        else:
            return 0.0
        
        if total == 0:
            return 0.0
        return winning / total
    
    def profit_loss_ratio(self) -> float:
        """计算盈亏比
        
        Returns:
            平均盈利 / 平均亏损
        """
        if self.trades is None or self.trades.empty:
            return 0.0
        
        profit_col = 'profit' if 'profit' in self.trades.columns else 'return'
        
        winning = self.trades[self.trades[profit_col] > 0][profit_col]
        losing = self.trades[self.trades[profit_col] < 0][profit_col]
        
        avg_win = winning.mean() if len(winning) > 0 else 0
        avg_loss = abs(losing.mean()) if len(losing) > 0 else 0
        
        if avg_loss == 0:
            return float('inf') if avg_win > 0 else 0
        return avg_win / avg_loss
    
    def sharpe_ratio(self, risk_free_rate: float = 0.03) -> float:
        """计算夏普比率
        
        Args:
            risk_free_rate: 无风险利率（年化）
            
        Returns:
            夏普比率
        """
        if self.returns is None or len(self.returns) == 0:
            return 0.0
        
        excess_returns = self.returns - risk_free_rate / 252
        if excess_returns.std() == 0:
            return 0.0
        return excess_returns.mean() / excess_returns.std() * np.sqrt(252)
    
    def max_drawdown(self) -> float:
        """计算最大回撤
        
        Returns:
            最大回撤比例（正值）
        """
        if self.returns is None or len(self.returns) == 0:
            return 0.0
        
        cumulative = (1 + self.returns).cumprod()
        peak = cumulative.expanding(min_periods=1).max()
        drawdown = (cumulative - peak) / peak
        return abs(drawdown.min())
    
    def annual_return(self) -> float:
        """计算年化收益率
        
        Returns:
            年化收益率
        """
        if self.returns is None or len(self.returns) == 0:
            return 0.0
        
        total_return = (1 + self.returns).prod() - 1
        days = len(self.returns)
        if days == 0:
            return 0.0
        return (1 + total_return) ** (252 / days) - 1
    
    def volatility(self) -> float:
        """计算年化波动率
        
        Returns:
            年化波动率
        """
        if self.returns is None or len(self.returns) == 0:
            return 0.0
        return self.returns.std() * np.sqrt(252)
    
    def calmar_ratio(self) -> float:
        """计算卡玛比率
        
        Returns:
            年化收益 / 最大回撤
        """
        dd = self.max_drawdown()
        if dd == 0:
            return 0.0
        return self.annual_return() / dd
    
    def sortino_ratio(self, risk_free_rate: float = 0.03) -> float:
        """计算索提诺比率
        
        Args:
            risk_free_rate: 无风险利率
            
        Returns:
            索提诺比率
        """
        if self.returns is None or len(self.returns) == 0:
            return 0.0
        
        excess_returns = self.returns - risk_free_rate / 252
        downside_returns = excess_returns[excess_returns < 0]
        
        if len(downside_returns) == 0:
            return float('inf')
        
        downside_std = downside_returns.std()
        if downside_std == 0:
            return 0.0
        
        return excess_returns.mean() / downside_std * np.sqrt(252)
    
    def get_all_metrics(self) -> Dict:
        """获取所有指标
        
        Returns:
            指标字典
        """
        return {
            'win_rate': self.win_rate(),
            'profit_loss_ratio': self.profit_loss_ratio(),
            'sharpe_ratio': self.sharpe_ratio(),
            'max_drawdown': self.max_drawdown(),
            'annual_return': self.annual_return(),
            'volatility': self.volatility(),
            'calmar_ratio': self.calmar_ratio(),
            'sortino_ratio': self.sortino_ratio(),
        }
    
    def print_summary(self):
        """打印摘要"""
        metrics = self.get_all_metrics()
        print("\n" + "="*50)
        print("绩效指标汇总")
        print("="*50)
        for key, value in metrics.items():
            print(f"{key:20s}: {value:.4f}")
        print("="*50)