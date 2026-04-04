# -*- coding: utf-8 -*-
"""Performance metrics calculation"""

from typing import Dict
import pandas as pd
import numpy as np


class PerformanceMetrics:
    """Performance metrics calculation"""
    
    def __init__(self, returns: pd.Series = None):
        self.returns = returns
    
    def win_rate(self) -> float:
        """Calculate win rate"""
        if self.returns is None:
            return 0.0
        winning = self.returns[self.returns > 0]
        total = len(self.returns[self.returns != 0])
        return len(winning) / total if total > 0 else 0.0
    
    def sharpe_ratio(self, rf: float = 0.03) -> float:
        """Calculate Sharpe ratio"""
        if self.returns is None or len(self.returns) == 0:
            return 0.0
        excess = self.returns - rf / 252
        if excess.std() == 0:
            return 0.0
        return excess.mean() / excess.std() * np.sqrt(252)
    
    def max_drawdown(self) -> float:
        """Calculate max drawdown"""
        if self.returns is None or len(self.returns) == 0:
            return 0.0
        cum = (1 + self.returns).cumprod()
        peak = cum.expanding(min_periods=1).max()
        return ((cum - peak) / peak).min()
    
    def get_all_metrics(self) -> Dict:
        """Get all metrics"""
        return {
            'win_rate': self.win_rate(),
            'sharpe_ratio': self.sharpe_ratio(),
            'max_drawdown': self.max_drawdown()
        }