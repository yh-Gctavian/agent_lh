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
    
    def __init__(self, returns: pd.Series = None):
        self.returns = returns
    
    def set_returns(self, returns: pd.Series):
        """设置收益率序列"""
        self.returns = returns
    
    def win_rate(self) -> float:
        """计算胜率
        
        Returns:
            胜率（盈利交易占比）
        """
        if self.returns is None or len(self.returns) == 0:
            return 0.0
        
        trades = self.returns[self.returns != 0]
        if len(trades) == 0:
            return 0.0
        
        winning = len(trades[trades > 0])
        return winning / len(trades)
    
    def profit_loss_ratio(self) -> float:
        """计算盈亏比
        
        Returns:
            平均盈利 / 平均亏损
        """
        if self.returns is None or len(self.returns) == 0:
            return 0.0
        
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
        if self.returns is None or len(self.returns) == 0:
            return 0.0
        
        excess_returns = self.returns - risk_free_rate / 252
        std = excess_returns.std()
        if std == 0:
            return 0.0
        return excess_returns.mean() / std * np.sqrt(252)
    
    def max_drawdown(self) -> float:
        """计算最大回撤
        
        Returns:
            最大回撤比例（负数）
        """
        if self.returns is None or len(self.returns) == 0:
            return 0.0
        
        cumulative = (1 + self.returns).cumprod()
        peak = cumulative.expanding(min_periods=1).max()
        drawdown = (cumulative - peak) / peak
        return drawdown.min()
    
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
            年化收益 / 最大回撤绝对值
        """
        mdd = abs(self.max_drawdown())
        if mdd == 0:
            return 0.0
        return self.annual_return() / mdd
    
    def get_all_metrics(self) -> Dict:
        """获取所有指标
        
        Returns:
            指标字典
        """
        return {
            'win_rate': round(self.win_rate() * 100, 2),
            'profit_loss_ratio': round(self.profit_loss_ratio(), 2),
            'sharpe_ratio': round(self.sharpe_ratio(), 2),
            'max_drawdown': round(self.max_drawdown() * 100, 2),
            'annual_return': round(self.annual_return() * 100, 2),
            'volatility': round(self.volatility() * 100, 2),
            'calmar_ratio': round(self.calmar_ratio(), 2),
        }
    
    def calculate_from_trades(self, trades: pd.DataFrame) -> Dict:
        """从交易记录计算指标
        
        Args:
            trades: 交易记录DataFrame
            
        Returns:
            指标字典
        """
        if trades.empty:
            return self.get_all_metrics()
        
        # 计算每笔交易收益
        if 'profit' in trades.columns:
            self.returns = trades['profit'] / trades['cost']
        elif 'return' in trades.columns:
            self.returns = trades['return']
        
        return self.get_all_metrics()
    
    def calculate_from_daily(self, daily_values: pd.DataFrame) -> Dict:
        """从每日净值计算指标
        
        Args:
            daily_values: 每日净值DataFrame
            
        Returns:
            指标字典
        """
        if daily_values.empty:
            return self.get_all_metrics()
        
        if 'value' in daily_values.columns:
            self.returns = daily_values['value'].pct_change()
        elif 'return' in daily_values.columns:
            self.returns = daily_values['return']
        
        return self.get_all_metrics()