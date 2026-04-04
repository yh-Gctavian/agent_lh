# -*- coding: utf-8 -*-
"""绩效指标计算"""

from typing import Dict, List
import pandas as pd
import numpy as np

from utils.logger import get_logger

logger = get_logger('performance_metrics')


class PerformanceMetrics:
    """绩效指标计算
    
    核心指标：
    - 胜率
    - 盈亏比
    - 夏普比率
    - 最大回撤
    - 年化收益
    """
    
    def __init__(self, returns: pd.Series = None, trade_records: pd.DataFrame = None):
        self.returns = returns
        self.trade_records = trade_records
    
    def win_rate(self) -> float:
        """计算胜率
        
        Returns:
            胜率（盈利交易占比）
        """
        if self.trade_records is None or self.trade_records.empty:
            return 0.0
        
        sells = self.trade_records[self.trade_records['direction'] == 'sell']
        if sells.empty:
            return 0.0
        
        # 计算每笔交易盈亏
        profits = []
        for _, sell in sells.iterrows():
            symbol = sell['symbol']
            sell_price = sell['price']
            sell_date = sell['date']
            
            # 找对应的买入记录
            buys = self.trade_records[
                (self.trade_records['symbol'] == symbol) &
                (self.trade_records['direction'] == 'buy') &
                (self.trade_records['date'] < sell_date)
            ]
            
            if not buys.empty:
                buy_price = buys.iloc[-1]['price']
                profit = (sell_price - buy_price) / buy_price
                profits.append(profit)
        
        if not profits:
            return 0.0
        
        wins = [p for p in profits if p > 0]
        return len(wins) / len(profits)
    
    def profit_loss_ratio(self) -> float:
        """计算盈亏比
        
        Returns:
            平均盈利 / 平均亏损
        """
        if self.trade_records is None or self.trade_records.empty:
            return 0.0
        
        sells = self.trade_records[self.trade_records['direction'] == 'sell']
        if sells.empty:
            return 0.0
        
        profits = []
        for _, sell in sells.iterrows():
            symbol = sell['symbol']
            sell_price = sell['price']
            sell_date = sell['date']
            
            buys = self.trade_records[
                (self.trade_records['symbol'] == symbol) &
                (self.trade_records['direction'] == 'buy') &
                (self.trade_records['date'] < sell_date)
            ]
            
            if not buys.empty:
                buy_price = buys.iloc[-1]['price']
                profit = (sell_price - buy_price) / buy_price
                profits.append(profit)
        
        if not profits:
            return 0.0
        
        wins = [p for p in profits if p > 0]
        losses = [p for p in profits if p < 0]
        
        avg_win = np.mean(wins) if wins else 0
        avg_loss = abs(np.mean(losses)) if losses else 0
        
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
        if self.returns is None or self.returns.empty:
            return 0.0
        
        excess = self.returns - risk_free_rate / 252
        
        if excess.std() == 0:
            return 0.0
        
        return excess.mean() / excess.std() * np.sqrt(252)
    
    def max_drawdown(self) -> float:
        """计算最大回撤
        
        Returns:
            最大回撤比例（负数）
        """
        if self.returns is None or self.returns.empty:
            return 0.0
        
        cum = (1 + self.returns).cumprod()
        peak = cum.expanding(min_periods=1).max()
        drawdown = (cum - peak) / peak
        
        return drawdown.min()
    
    def annual_return(self) -> float:
        """计算年化收益率
        
        Returns:
            年化收益率
        """
        if self.returns is None or self.returns.empty:
            return 0.0
        
        total = (1 + self.returns).prod() - 1
        days = len(self.returns)
        
        if days == 0:
            return 0.0
        
        return (1 + total) ** (252 / days) - 1
    
    def total_return(self) -> float:
        """计算总收益率"""
        if self.returns is None or self.returns.empty:
            return 0.0
        
        return (1 + self.returns).prod() - 1
    
    def volatility(self) -> float:
        """计算年化波动率"""
        if self.returns is None or self.returns.empty:
            return 0.0
        
        return self.returns.std() * np.sqrt(252)
    
    def calmar_ratio(self) -> float:
        """计算卡玛比率（年化收益/最大回撤）"""
        ann_ret = self.annual_return()
        max_dd = abs(self.max_drawdown())
        
        if max_dd == 0:
            return 0.0
        
        return ann_ret / max_dd
    
    def get_all_metrics(self) -> Dict:
        """获取所有指标
        
        Returns:
            指标字典
        """
        return {
            'total_return': self.total_return(),
            'annual_return': self.annual_return(),
            'max_drawdown': self.max_drawdown(),
            'sharpe_ratio': self.sharpe_ratio(),
            'win_rate': self.win_rate(),
            'profit_loss_ratio': self.profit_loss_ratio(),
            'volatility': self.volatility(),
            'calmar_ratio': self.calmar_ratio(),
        }
    
    def print_summary(self):
        """打印摘要"""
        metrics = self.get_all_metrics()
        
        print("\n" + "=" * 50)
        print("策略绩效摘要")
        print("=" * 50)
        print(f"总收益率:     {metrics['total_return']*100:.2f}%")
        print(f"年化收益率:   {metrics['annual_return']*100:.2f}%")
        print(f"最大回撤:     {metrics['max_drawdown']*100:.2f}%")
        print(f"夏普比率:     {metrics['sharpe_ratio']:.2f}")
        print(f"胜率:         {metrics['win_rate']*100:.2f}%")
        print(f"盈亏比:       {metrics['profit_loss_ratio']:.2f}")
        print(f"年化波动率:   {metrics['volatility']*100:.2f}%")
        print(f"卡玛比率:     {metrics['calmar_ratio']:.2f}")
        print("=" * 50 + "\n")