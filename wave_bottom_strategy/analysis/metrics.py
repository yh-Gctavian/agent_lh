# -*- coding: utf-8 -*-
"""Performance metrics calculation"""

import pandas as pd
import numpy as np


class PerformanceMetrics:
    """Calculate performance metrics: win rate, profit/loss ratio, Sharpe, etc."""
    
    def __init__(self, returns: pd.Series = None, trade_returns: pd.Series = None):
        self.returns = returns
        self.trade_returns = trade_returns
    
    def win_rate(self) -> float:
        """Calculate win rate"""
        if self.trade_returns is None or len(self.trade_returns) == 0:
            return 0.0
        winning = self.trade_returns[self.trade_returns > 0]
        total = len(self.trade_returns[self.trade_returns != 0])
        return len(winning) / total if total > 0 else 0.0
    
    def profit_loss_ratio(self) -> float:
        """Calculate profit/loss ratio"""
        if self.trade_returns is None:
            return 0.0
        winning = self.trade_returns[self.trade_returns > 0]
        losing = self.trade_returns[self.trade_returns < 0]
        avg_win = winning.mean() if len(winning) > 0 else 0
        avg_loss = abs(losing.mean()) if len(losing) > 0 else 0
        return avg_win / avg_loss if avg_loss > 0 else 0.0
    
    def sharpe_ratio(self, risk_free_rate: float = 0.03) -> float:
        """Calculate Sharpe ratio"""
        if self.returns is None or len(self.returns) == 0:
            return 0.0
        excess = self.returns - risk_free_rate / 252
        std = excess.std()
        return excess.mean() / std * np.sqrt(252) if std > 0 else 0.0
    
    def max_drawdown(self) -> float:
        """Calculate maximum drawdown"""
        if self.returns is None or len(self.returns) == 0:
            return 0.0
        cumulative = (1 + self.returns).cumprod()
        peak = cumulative.expanding(min_periods=1).max()
        drawdown = (cumulative - peak) / peak
        return drawdown.min()
    
    def annual_return(self) -> float:
        """Calculate annualized return"""
        if self.returns is None or len(self.returns) == 0:
            return 0.0
        total = (1 + self.returns).prod() - 1
        days = len(self.returns)
        return (1 + total) ** (252 / days) - 1 if days > 0 else 0.0
    
    def get_all_metrics(self) -> dict:
        """Get all metrics"""
        return {
            'win_rate': self.win_rate(),
            'profit_loss_ratio': self.profit_loss_ratio(),
            'sharpe_ratio': self.sharpe_ratio(),
            'max_drawdown': self.max_drawdown(),
            'annual_return': self.annual_return(),
        }