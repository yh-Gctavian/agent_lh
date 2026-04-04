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
    
    def win_rate(self) -> float:
        """计算胜率
        
        Returns:
            胜率（盈利交易占比）
        """
        if self.returns is None or len(self.returns) == 0:
            return 0.0
        
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
        if self.returns is None:
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
        
        if excess_returns.std() == 0:
            return 0.0
        
        return excess_returns.mean() / excess_returns.std() * np.sqrt(252)
    
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
            年化收益 / 最大回撤
        """
        max_dd = abs(self.max_drawdown())
        if max_dd == 0:
            return 0.0
        
        return self.annual_return() / max_dd
    
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
        downside_returns = self.returns[self.returns < 0]
        
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
    
    def summary(self) -> str:
        """生成摘要文本
        
        Returns:
            摘要文本
        """
        metrics = self.get_all_metrics()
        
        lines = [
            "=== 绩效指标摘要 ===",
            f"胜率: {metrics['win_rate']:.2%}",
            f"盈亏比: {metrics['profit_loss_ratio']:.2f}",
            f"夏普比率: {metrics['sharpe_ratio']:.2f}",
            f"最大回撤: {metrics['max_drawdown']:.2%}",
            f"年化收益: {metrics['annual_return']:.2%}",
            f"年化波动: {metrics['volatility']:.2%}",
            f"卡玛比率: {metrics['calmar_ratio']:.2f}",
            f"索提诺比率: {metrics['sortino_ratio']:.2f}",
        ]
        
        return "\n".join(lines)