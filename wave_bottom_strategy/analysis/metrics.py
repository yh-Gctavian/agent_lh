# -*- coding: utf-8 -*-
"""绩效指标计算"""

from typing import Dict
import pandas as pd
import numpy as np


class PerformanceMetrics:
    """绩效指标计算
    
    计算胜率、盈亏比、夏普比率等核心指标
    """
    
    def __init__(self, returns: pd.Series):
        self.returns = returns
    
    def win_rate(self) -> float:
        """计算胜率
        
        Returns:
            胜率（盈利交易占比）
        """
        winning = self.returns[self.returns > 0]
        total = len(self.returns[self.returns != 0])
        if total == 0:
            return 0.0
        return len(winning) / total
    
    def profit_loss_ratio(self) -> float:
        """计算盈亏比
        
        Returns:
            平均盈利 / 平均亏损
        """
        winning = self.returns[self.returns > 0]
        losing = self.returns[self.returns < 0]
        
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
        excess_returns = self.returns - risk_free_rate / 252
        if excess_returns.std() == 0:
            return 0.0
        return excess_returns.mean() / excess_returns.std() * np.sqrt(252)
    
    def max_drawdown(self) -> float:
        """计算最大回撤
        
        Returns:
            最大回撤比例
        """
        cumulative = (1 + self.returns).cumprod()
        peak = cumulative.expanding(min_periods=1).max()
        drawdown = (cumulative - peak) / peak
        return drawdown.min()
    
    def annual_return(self) -> float:
        """计算年化收益率
        
        Returns:
            年化收益率
        """
        total_return = (1 + self.returns).prod() - 1
        days = len(self.returns)
        return (1 + total_return) ** (252 / days) - 1
    
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
        }