# -*- coding: utf-8 -*-
"""绩效指标计算"""

from typing import Dict
import pandas as pd
import numpy as np

from utils.logger import get_logger

logger = get_logger('performance_metrics')


class PerformanceMetrics:
    """绩效指标计算
    
    计算胜率、盈亏比、夏普比率等核心指标
    """
    
    def __init__(self, returns: pd.Series = None):
        self.returns = returns
    
    def set_returns(self, returns: pd.Series):
        """设置收益率序列"""
        self.returns = returns
    
    def total_return(self) -> float:
        """总收益率"""
        if self.returns is None or len(self.returns) == 0:
            return 0.0
        return (1 + self.returns.fillna(0)).prod() - 1
    
    def annual_return(self) -> float:
        """年化收益率"""
        if self.returns is None or len(self.returns) == 0:
            return 0.0
        total = self.total_return()
        days = len(self.returns)
        if days == 0:
            return 0.0
        return (1 + total) ** (252 / days) - 1
    
    def volatility(self) -> float:
        """年化波动率"""
        if self.returns is None or len(self.returns) == 0:
            return 0.0
        return self.returns.std() * np.sqrt(252)
    
    def sharpe_ratio(self, risk_free_rate: float = 0.03) -> float:
        """夏普比率"""
        if self.returns is None or len(self.returns) == 0:
            return 0.0
        excess = self.returns - risk_free_rate / 252
        if excess.std() == 0:
            return 0.0
        return excess.mean() / excess.std() * np.sqrt(252)
    
    def max_drawdown(self) -> float:
        """最大回撤"""
        if self.returns is None or len(self.returns) == 0:
            return 0.0
        cum = (1 + self.returns.fillna(0)).cumprod()
        peak = cum.expanding(min_periods=1).max()
        drawdown = (cum - peak) / peak
        return drawdown.min()
    
    def calmar_ratio(self) -> float:
        """卡玛比率"""
        max_dd = abs(self.max_drawdown())
        if max_dd == 0:
            return 0.0
        return self.annual_return() / max_dd
    
    def win_rate(self, trade_returns: pd.Series = None) -> float:
        """胜率"""
        if trade_returns is not None:
            r = trade_returns
        elif self.returns is not None:
            r = self.returns
        else:
            return 0.0
        
        r = r[r != 0]
        if len(r) == 0:
            return 0.0
        
        wins = len(r[r > 0])
        return wins / len(r)
    
    def profit_loss_ratio(self, trade_returns: pd.Series = None) -> float:
        """盈亏比"""
        if trade_returns is not None:
            r = trade_returns
        elif self.returns is not None:
            r = self.returns
        else:
            return 0.0
        
        wins = r[r > 0]
        losses = r[r < 0]
        
        avg_win = wins.mean() if len(wins) > 0 else 0
        avg_loss = abs(losses.mean()) if len(losses) > 0 else 0
        
        if avg_loss == 0:
            return float('inf') if avg_win > 0 else 0.0
        return avg_win / avg_loss
    
    def get_all_metrics(self) -> Dict:
        """获取所有指标"""
        return {
            'total_return': self.total_return(),
            'annual_return': self.annual_return(),
            'volatility': self.volatility(),
            'sharpe_ratio': self.sharpe_ratio(),
            'max_drawdown': self.max_drawdown(),
            'calmar_ratio': self.calmar_ratio(),
            'win_rate': self.win_rate(),
            'profit_loss_ratio': self.profit_loss_ratio()
        }
    
    @staticmethod
    def calculate_from_values(values: pd.Series) -> Dict:
        """从净值序列计算指标"""
        returns = values.pct_change()
        metrics = PerformanceMetrics(returns)
        return metrics.get_all_metrics()