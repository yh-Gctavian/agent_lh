# -*- coding: utf-8 -*-
"""绩效指标计算"""

from typing import Dict, List
import pandas as pd
import numpy as np

from utils.logger import get_logger

logger = get_logger('performance_metrics')


class PerformanceMetrics:
    """绩效指标计算
    
    计算胜率、盈亏比、夏普比率、最大回撤等核心指标
    """
    
    def __init__(self, daily_values: pd.DataFrame = None):
        """初始化
        
        Args:
            daily_values: 每日净值数据，需包含 date, total_value 列
        """
        self.daily_values = daily_values
    
    def calculate_returns(self) -> pd.Series:
        """计算日收益率"""
        if self.daily_values is None or 'total_value' not in self.daily_values.columns:
            return pd.Series()
        
        return self.daily_values['total_value'].pct_change()
    
    def win_rate(self, trades: pd.DataFrame = None) -> float:
        """计算胜率
        
        Args:
            trades: 交易记录，需包含 profit 列
            
        Returns:
            胜率（盈利交易占比）
        """
        if trades is None or trades.empty:
            return 0.0
        
        if 'profit' not in trades.columns:
            return 0.0
        
        winning = trades[trades['profit'] > 0]
        total = trades[trades['profit'] != 0]
        
        if len(total) == 0:
            return 0.0
        
        return len(winning) / len(total)
    
    def profit_loss_ratio(self, trades: pd.DataFrame = None) -> float:
        """计算盈亏比
        
        Args:
            trades: 交易记录
            
        Returns:
            平均盈利 / 平均亏损
        """
        if trades is None or trades.empty or 'profit' not in trades.columns:
            return 0.0
        
        winning = trades[trades['profit'] > 0]
        losing = trades[trades['profit'] < 0]
        
        avg_win = winning['profit'].mean() if len(winning) > 0 else 0
        avg_loss = abs(losing['profit'].mean()) if len(losing) > 0 else 0
        
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
        returns = self.calculate_returns()
        
        if returns.empty or returns.std() == 0:
            return 0.0
        
        # 日无风险利率
        daily_rf = risk_free_rate / 252
        
        # 超额收益
        excess_returns = returns - daily_rf
        
        # 夏普比率 = 超额收益均值 / 标准差 * sqrt(252)
        sharpe = excess_returns.mean() / excess_returns.std() * np.sqrt(252)
        
        return sharpe
    
    def max_drawdown(self) -> float:
        """计算最大回撤
        
        Returns:
            最大回撤比例（负数）
        """
        if self.daily_values is None or 'total_value' not in self.daily_values.columns:
            return 0.0
        
        values = self.daily_values['total_value']
        
        # 累计最大值
        peak = values.expanding(min_periods=1).max()
        
        # 回撤
        drawdown = (values - peak) / peak
        
        return drawdown.min()
    
    def annual_return(self) -> float:
        """计算年化收益率
        
        Returns:
            年化收益率
        """
        if self.daily_values is None or 'total_value' not in self.daily_values.columns:
            return 0.0
        
        values = self.daily_values['total_value']
        
        if len(values) < 2:
            return 0.0
        
        total_return = values.iloc[-1] / values.iloc[0] - 1
        days = len(values)
        
        # 年化
        annual = (1 + total_return) ** (252 / days) - 1
        
        return annual
    
    def total_return(self) -> float:
        """计算总收益率"""
        if self.daily_values is None or 'total_value' not in self.daily_values.columns:
            return 0.0
        
        values = self.daily_values['total_value']
        
        if len(values) < 2:
            return 0.0
        
        return values.iloc[-1] / values.iloc[0] - 1
    
    def volatility(self) -> float:
        """计算年化波动率"""
        returns = self.calculate_returns()
        
        if returns.empty:
            return 0.0
        
        return returns.std() * np.sqrt(252)
    
    def calmar_ratio(self) -> float:
        """计算卡玛比率（年化收益/最大回撤）"""
        ann_ret = self.annual_return()
        max_dd = abs(self.max_drawdown())
        
        if max_dd == 0:
            return 0.0
        
        return ann_ret / max_dd
    
    def sortino_ratio(self, risk_free_rate: float = 0.03) -> float:
        """计算索提诺比率"""
        returns = self.calculate_returns()
        
        if returns.empty:
            return 0.0
        
        # 下行波动率
        negative_returns = returns[returns < 0]
        downside_std = negative_returns.std() * np.sqrt(252)
        
        if downside_std == 0:
            return 0.0
        
        ann_ret = self.annual_return()
        
        return (ann_ret - risk_free_rate) / downside_std
    
    def get_all_metrics(self, trades: pd.DataFrame = None) -> Dict:
        """获取所有指标
        
        Args:
            trades: 交易记录
            
        Returns:
            指标字典
        """
        return {
            'total_return': f"{self.total_return():.2%}",
            'annual_return': f"{self.annual_return():.2%}",
            'sharpe_ratio': f"{self.sharpe_ratio():.2f}",
            'max_drawdown': f"{self.max_drawdown():.2%}",
            'volatility': f"{self.volatility():.2%}",
            'calmar_ratio': f"{self.calmar_ratio():.2f}",
            'sortino_ratio': f"{self.sortino_ratio():.2f}",
            'win_rate': f"{self.win_rate(trades):.2%}",
            'profit_loss_ratio': f"{self.profit_loss_ratio(trades):.2f}",
        }
    
    def get_summary_table(self, trades: pd.DataFrame = None) -> pd.DataFrame:
        """获取指标汇总表"""
        metrics = self.get_all_metrics(trades)
        
        df = pd.DataFrame([
            {'指标': k, '值': v} for k, v in metrics.items()
        ])
        
        return df


def calculate_trade_metrics(trades: pd.DataFrame) -> Dict:
    """计算交易相关指标
    
    Args:
        trades: 交易记录
        
    Returns:
        交易指标
    """
    if trades is None or trades.empty:
        return {}
    
    # 买入交易
    buys = trades[trades['direction'] == 'buy'] if 'direction' in trades.columns else trades
    
    # 卖出交易
    sells = trades[trades['direction'] == 'sell'] if 'direction' in trades.columns else trades
    
    total_trades = len(trades)
    buy_count = len(buys)
    sell_count = len(sells)
    
    return {
        'total_trades': total_trades,
        'buy_count': buy_count,
        'sell_count': sell_count,
        'avg_trade_size': trades['shares'].mean() if 'shares' in trades.columns else 0,
    }