# -*- coding: utf-8 -*-
"""绩效指标计算"""

from typing import Dict, List
import pandas as pd
import numpy as np

from ..utils.logger import get_logger

logger = get_logger('metrics')


class PerformanceMetrics:
    """绩效指标计算
    
    计算胜率、盈亏比、夏普比率等核心指标
    """
    
    def __init__(self, returns: pd.Series = None, trades: List[Dict] = None):
        """初始化
        
        Args:
            returns: 日收益率序列
            trades: 交易记录
        """
        self.returns = returns
        self.trades = trades or []
    
    def total_return(self) -> float:
        """总收益率"""
        if self.returns is None or len(self.returns) == 0:
            return 0.0
        return (1 + self.returns).prod() - 1
    
    def annual_return(self) -> float:
        """年化收益率"""
        if self.returns is None or len(self.returns) == 0:
            return 0.0
        
        total = (1 + self.returns).prod() - 1
        days = len(self.returns)
        
        return (1 + total) ** (252 / days) - 1
    
    def volatility(self) -> float:
        """年化波动率"""
        if self.returns is None or len(self.returns) == 0:
            return 0.0
        return self.returns.std() * np.sqrt(252)
    
    def sharpe_ratio(self, risk_free_rate: float = 0.03) -> float:
        """夏普比率
        
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
        """最大回撤"""
        if self.returns is None or len(self.returns) == 0:
            return 0.0
        
        cumulative = (1 + self.returns).cumprod()
        peak = cumulative.expanding(min_periods=1).max()
        drawdown = (cumulative - peak) / peak
        
        return drawdown.min()
    
    def calmar_ratio(self) -> float:
        """卡玛比率"""
        max_dd = abs(self.max_drawdown())
        if max_dd == 0:
            return 0.0
        return self.annual_return() / max_dd
    
    def sortino_ratio(self, risk_free_rate: float = 0.03) -> float:
        """索提诺比率"""
        if self.returns is None or len(self.returns) == 0:
            return 0.0
        
        excess_returns = self.returns - risk_free_rate / 252
        downside_returns = excess_returns[excess_returns < 0]
        
        if len(downside_returns) == 0:
            return float('inf')
        
        downside_std = downside_returns.std() * np.sqrt(252)
        
        if downside_std == 0:
            return 0.0
        
        return excess_returns.mean() * 252 / downside_std
    
    def win_rate(self) -> float:
        """胜率（盈利交易占比）"""
        if not self.trades:
            return 0.0
        
        profitable = [t for t in self.trades if t.get('profit', 0) > 0]
        total = [t for t in self.trades if t.get('profit', 0) != 0]
        
        if len(total) == 0:
            return 0.0
        
        return len(profitable) / len(total)
    
    def profit_loss_ratio(self) -> float:
        """盈亏比"""
        if not self.trades:
            return 0.0
        
        profits = [t.get('profit', 0) for t in self.trades if t.get('profit', 0) > 0]
        losses = [abs(t.get('profit', 0)) for t in self.trades if t.get('profit', 0) < 0]
        
        avg_profit = np.mean(profits) if profits else 0
        avg_loss = np.mean(losses) if losses else 0
        
        if avg_loss == 0:
            return float('inf') if avg_profit > 0 else 0
        
        return avg_profit / avg_loss
    
    def trade_count(self) -> int:
        """交易次数"""
        return len(self.trades)
    
    def avg_holding_days(self) -> float:
        """平均持仓天数"""
        if not self.trades:
            return 0.0
        
        days = [t.get('holding_days', 0) for t in self.trades]
        return np.mean(days) if days else 0
    
    def get_all_metrics(self) -> Dict:
        """获取所有指标
        
        Returns:
            指标字典
        """
        return {
            'total_return': self.total_return(),
            'annual_return': self.annual_return(),
            'volatility': self.volatility(),
            'sharpe_ratio': self.sharpe_ratio(),
            'max_drawdown': self.max_drawdown(),
            'calmar_ratio': self.calmar_ratio(),
            'sortino_ratio': self.sortino_ratio(),
            'win_rate': self.win_rate(),
            'profit_loss_ratio': self.profit_loss_ratio(),
            'trade_count': self.trade_count(),
            'avg_holding_days': self.avg_holding_days()
        }
    
    def compare_benchmark(
        self,
        benchmark_returns: pd.Series
    ) -> Dict:
        """对比基准
        
        Args:
            benchmark_returns: 基准收益率
            
        Returns:
            对比结果
        """
        if self.returns is None or benchmark_returns is None:
            return {}
        
        # 对齐
        common_idx = self.returns.index.intersection(benchmark_returns.index)
        
        if len(common_idx) == 0:
            return {}
        
        strategy = self.returns.loc[common_idx]
        benchmark = benchmark_returns.loc[common_idx]
        
        # 超额收益
        excess = strategy - benchmark
        
        return {
            'strategy_return': (1 + strategy).prod() - 1,
            'benchmark_return': (1 + benchmark).prod() - 1,
            'excess_return': (1 + excess).prod() - 1,
            'tracking_error': (strategy - benchmark).std() * np.sqrt(252),
            'information_ratio': excess.mean() / excess.std() * np.sqrt(252) if excess.std() > 0 else 0
        }