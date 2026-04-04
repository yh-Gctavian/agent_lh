# -*- coding: utf-8 -*-
"""绩效指标计算"""

from typing import Dict
import pandas as pd
import numpy as np

from utils.logger import get_logger

logger = get_logger('performance_metrics')


class PerformanceMetrics:
    """绩效指标计算"""
    
    def __init__(self, returns: pd.Series = None, daily_values: pd.DataFrame = None):
        self.returns = returns
        self.daily_values = daily_values
    
    def win_rate(self, trades: pd.DataFrame = None) -> float:
        """计算胜率"""
        if trades is None or trades.empty:
            return 0.0
        
        # 统计盈利交易
        profits = trades[trades['profit'] > 0] if 'profit' in trades.columns else pd.DataFrame()
        total = len(trades[trades['action'] == 'sell']) if 'action' in trades.columns else len(trades)
        
        if total == 0:
            return 0.0
        
        return len(profits) / total
    
    def profit_loss_ratio(self, trades: pd.DataFrame = None) -> float:
        """计算盈亏比"""
        if trades is None or trades.empty or 'profit' not in trades.columns:
            return 0.0
        
        profits = trades[trades['profit'] > 0]['profit']
        losses = trades[trades['profit'] < 0]['profit']
        
        avg_profit = profits.mean() if len(profits) > 0 else 0
        avg_loss = abs(losses.mean()) if len(losses) > 0 else 0
        
        if avg_loss == 0:
            return float('inf') if avg_profit > 0 else 0
        
        return avg_profit / avg_loss
    
    def sharpe_ratio(self, risk_free_rate: float = 0.03) -> float:
        """计算夏普比率"""
        if self.returns is None or self.returns.empty:
            return 0.0
        
        excess = self.returns - risk_free_rate / 252
        
        if excess.std() == 0:
            return 0.0
        
        return excess.mean() / excess.std() * np.sqrt(252)
    
    def max_drawdown(self) -> float:
        """计算最大回撤"""
        if self.daily_values is None or self.daily_values.empty:
            return 0.0
        
        values = self.daily_values['value'] if 'value' in self.daily_values.columns else self.daily_values.iloc[:, 0]
        
        cumulative = values
        peak = cumulative.expanding(min_periods=1).max()
        drawdown = (cumulative - peak) / peak
        
        return drawdown.min()
    
    def annual_return(self) -> float:
        """计算年化收益率"""
        if self.daily_values is None or len(self.daily_values) < 2:
            return 0.0
        
        values = self.daily_values['value'] if 'value' in self.daily_values.columns else self.daily_values.iloc[:, 0]
        
        total_return = values.iloc[-1] / values.iloc[0] - 1
        days = len(values)
        
        return (1 + total_return) ** (252 / days) - 1
    
    def volatility(self) -> float:
        """计算年化波动率"""
        if self.returns is None or self.returns.empty:
            return 0.0
        
        return self.returns.std() * np.sqrt(252)
    
    def calmar_ratio(self) -> float:
        """计算卡玛比率"""
        annual = self.annual_return()
        mdd = abs(self.max_drawdown())
        
        if mdd == 0:
            return 0.0
        
        return annual / mdd
    
    def get_all_metrics(self, trades: pd.DataFrame = None) -> Dict:
        """获取所有指标"""
        return {
            'win_rate': self.win_rate(trades),
            'profit_loss_ratio': self.profit_loss_ratio(trades),
            'sharpe_ratio': self.sharpe_ratio(),
            'max_drawdown': self.max_drawdown(),
            'annual_return': self.annual_return(),
            'volatility': self.volatility(),
            'calmar_ratio': self.calmar_ratio()
        }