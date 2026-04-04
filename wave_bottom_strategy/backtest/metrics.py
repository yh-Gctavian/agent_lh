# -*- coding: utf-8 -*-
"""绩效统计 - 收益率、夏普比率、最大回撤、胜率等"""

from typing import Dict, List, Optional, Tuple
from datetime import date
import pandas as pd
import numpy as np

from utils.logger import get_logger

logger = get_logger('metrics')


class PerformanceMetrics:
    """绩效指标计算器"""
    
    def __init__(self, risk_free_rate: float = 0.03):
        """
        Args:
            risk_free_rate: 无风险利率（年化）
        """
        self.risk_free_rate = risk_free_rate
    
    def calc_returns(self, daily_values: pd.DataFrame) -> pd.Series:
        """计算日收益率
        
        Args:
            daily_values: 每日资产数据
            
        Returns:
            日收益率序列
        """
        if daily_values.empty or 'total_value' not in daily_values.columns:
            return pd.Series()
        
        values = daily_values['total_value']
        returns = values.pct_change()
        returns.iloc[0] = 0  # 第一天收益率为0
        
        return returns
    
    def calc_cumulative_return(self, daily_values: pd.DataFrame) -> float:
        """计算累计收益率
        
        Args:
            daily_values: 每日资产数据
            
        Returns:
            累计收益率
        """
        if daily_values.empty or 'total_value' not in daily_values.columns:
            return 0.0
        
        start_value = daily_values['total_value'].iloc[0]
        end_value = daily_values['total_value'].iloc[-1]
        
        if start_value == 0:
            return 0.0
        
        return (end_value - start_value) / start_value
    
    def calc_annualized_return(self, daily_values: pd.DataFrame) -> float:
        """计算年化收益率
        
        Args:
            daily_values: 每日资产数据
            
        Returns:
            年化收益率
        """
        if daily_values.empty:
            return 0.0
        
        cumulative = self.calc_cumulative_return(daily_values)
        
        # 计算交易天数
        n_days = len(daily_values)
        if n_days == 0:
            return 0.0
        
        # 年化
        annualized = (1 + cumulative) ** (252 / n_days) - 1
        
        return annualized
    
    def calc_volatility(self, daily_values: pd.DataFrame) -> float:
        """计算年化波动率
        
        Args:
            daily_values: 每日资产数据
            
        Returns:
            年化波动率
        """
        returns = self.calc_returns(daily_values)
        
        if returns.empty:
            return 0.0
        
        # 日收益率标准差 * sqrt(252)
        return returns.std() * np.sqrt(252)
    
    def calc_sharpe_ratio(self, daily_values: pd.DataFrame) -> float:
        """计算夏普比率
        
        Args:
            daily_values: 每日资产数据
            
        Returns:
            夏普比率
        """
        annualized_return = self.calc_annualized_return(daily_values)
        volatility = self.calc_volatility(daily_values)
        
        if volatility == 0:
            return 0.0
        
        return (annualized_return - self.risk_free_rate) / volatility
    
    def calc_max_drawdown(self, daily_values: pd.DataFrame) -> Dict:
        """计算最大回撤
        
        Args:
            daily_values: 每日资产数据
            
        Returns:
            最大回撤信息
        """
        if daily_values.empty or 'total_value' not in daily_values.columns:
            return {'max_drawdown': 0, 'start_date': None, 'end_date': None}
        
        values = daily_values['total_value']
        
        # 计算累计最大值
        cummax = values.cummax()
        
        # 计算回撤
        drawdown = (values - cummax) / cummax
        
        # 最大回撤
        max_dd = drawdown.min()
        
        # 找到最大回撤的起止日期
        end_idx = drawdown.idxmin()
        end_date = daily_values.loc[end_idx, 'date'] if 'date' in daily_values.columns else None
        
        # 找起始日期（回撤开始前的最高点）
        start_idx = values[:end_idx].idxmax()
        start_date = daily_values.loc[start_idx, 'date'] if 'date' in daily_values.columns else None
        
        return {
            'max_drawdown': abs(max_dd),
            'start_date': start_date,
            'end_date': end_date,
            'drawdown_series': drawdown
        }
    
    def calc_calmar_ratio(self, daily_values: pd.DataFrame) -> float:
        """计算卡玛比率（年化收益/最大回撤）
        
        Args:
            daily_values: 每日资产数据
            
        Returns:
            卡玛比率
        """
        annualized_return = self.calc_annualized_return(daily_values)
        max_dd_info = self.calc_max_drawdown(daily_values)
        max_dd = max_dd_info['max_drawdown']
        
        if max_dd == 0:
            return 0.0
        
        return annualized_return / max_dd
    
    def calc_sortino_ratio(self, daily_values: pd.DataFrame) -> float:
        """计算索提诺比率（只考虑下行风险）
        
        Args:
            daily_values: 每日资产数据
            
        Returns:
            索提诺比率
        """
        returns = self.calc_returns(daily_values)
        
        if returns.empty:
            return 0.0
        
        # 下行收益率（只计算负收益）
        downside_returns = returns[returns < 0]
        
        if downside_returns.empty:
            return float('inf')  # 没有亏损
        
        # 下行标准差
        downside_std = downside_returns.std() * np.sqrt(252)
        
        annualized_return = self.calc_annualized_return(daily_values)
        
        if downside_std == 0:
            return 0.0
        
        return (annualized_return - self.risk_free_rate) / downside_std
    
    def calc_win_rate(self, trade_records: pd.DataFrame) -> Dict:
        """计算胜率
        
        Args:
            trade_records: 交易记录
            
        Returns:
            胜率相关信息
        """
        if trade_records.empty:
            return {
                'win_rate': 0,
                'win_count': 0,
                'loss_count': 0,
                'total_trades': 0
            }
        
        # 需要配对的买卖记录来计算盈亏
        # 简化处理：统计卖出交易
        sells = trade_records[trade_records['direction'] == 'sell'].copy()
        
        if sells.empty:
            return {
                'win_rate': 0,
                'win_count': 0,
                'loss_count': 0,
                'total_trades': 0
            }
        
        # 这里需要持仓成本信息来计算盈亏
        # 暂时返回卖出次数
        return {
            'win_rate': 0,
            'win_count': 0,
            'loss_count': 0,
            'total_trades': len(sells)
        }
    
    def calc_profit_factor(self, trade_records: pd.DataFrame) -> float:
        """计算盈亏比
        
        Args:
            trade_records: 交易记录
            
        Returns:
            盈亏比
        """
        # 需要更详细的交易记录才能计算
        return 0.0
    
    def calc_avg_holding_days(self, trade_records: pd.DataFrame) -> float:
        """计算平均持仓天数
        
        Args:
            trade_records: 交易记录
            
        Returns:
            平均持仓天数
        """
        # 需要持仓天数信息
        return 0.0
    
    def generate_report(
        self,
        daily_values: pd.DataFrame,
        trade_records: pd.DataFrame = None,
        benchmark_values: pd.DataFrame = None
    ) -> Dict:
        """生成绩效报告
        
        Args:
            daily_values: 每日资产数据
            trade_records: 交易记录
            benchmark_values: 基准资产数据
            
        Returns:
            绩效报告字典
        """
        if daily_values.empty:
            return {}
        
        report = {
            # 收益指标
            'cumulative_return': self.calc_cumulative_return(daily_values),
            'annualized_return': self.calc_annualized_return(daily_values),
            
            # 风险指标
            'volatility': self.calc_volatility(daily_values),
            'max_drawdown': self.calc_max_drawdown(daily_values)['max_drawdown'],
            'max_drawdown_info': self.calc_max_drawdown(daily_values),
            
            # 风险调整收益
            'sharpe_ratio': self.calc_sharpe_ratio(daily_values),
            'calmar_ratio': self.calc_calmar_ratio(daily_values),
            'sortino_ratio': self.calc_sortino_ratio(daily_values),
            
            # 交易指标
            'trade_stats': {}
        }
        
        # 添加交易统计
        if trade_records is not None and not trade_records.empty:
            report['trade_stats'] = {
                'total_trades': len(trade_records),
                'buy_count': len(trade_records[trade_records['direction'] == 'buy']),
                'sell_count': len(trade_records[trade_records['direction'] == 'sell']),
                'total_commission': trade_records['commission'].sum() if 'commission' in trade_records.columns else 0,
                'total_stamp_duty': trade_records['stamp_duty'].sum() if 'stamp_duty' in trade_records.columns else 0,
                'total_transfer_fee': trade_records['transfer_fee'].sum() if 'transfer_fee' in trade_records.columns else 0
            }
        
        # 添加基准对比
        if benchmark_values is not None and not benchmark_values.empty:
            bench_return = self.calc_cumulative_return(benchmark_values)
            report['benchmark'] = {
                'benchmark_return': bench_return,
                'excess_return': report['cumulative_return'] - bench_return
            }
        
        return report


class TradeAnalyzer:
    """交易分析器"""
    
    def __init__(self):
        self.trades: List[dict] = []
    
    def add_trade(self, trade: dict):
        """添加交易记录"""
        self.trades.append(trade)
    
    def analyze_trades(self, trade_records: pd.DataFrame) -> Dict:
        """分析交易记录
        
        Args:
            trade_records: 交易记录DataFrame
            
        Returns:
            交易分析结果
        """
        if trade_records.empty:
            return {}
        
        buys = trade_records[trade_records['direction'] == 'buy']
        sells = trade_records[trade_records['direction'] == 'sell']
        
        # 按股票分组计算盈亏
        trade_pnl = []
        
        for ts_code in buys['ts_code'].unique():
            stock_buys = buys[buys['ts_code'] == ts_code].sort_values('trade_date')
            stock_sells = sells[sells['ts_code'] == ts_code].sort_values('trade_date')
            
            # FIFO匹配买卖
            buy_queue = []
            for _, buy in stock_buys.iterrows():
                buy_queue.append({
                    'shares': buy['shares'],
                    'price': buy['price'],
                    'date': buy['trade_date']
                })
            
            for _, sell in stock_sells.iterrows():
                remaining = sell['shares']
                sell_price = sell['price']
                
                while remaining > 0 and buy_queue:
                    buy = buy_queue[0]
                    matched_shares = min(remaining, buy['shares'])
                    
                    pnl = (sell_price - buy['price']) * matched_shares
                    pnl_pct = (sell_price - buy['price']) / buy['price']
                    
                    trade_pnl.append({
                        'ts_code': ts_code,
                        'buy_date': buy['date'],
                        'sell_date': sell['trade_date'],
                        'shares': matched_shares,
                        'buy_price': buy['price'],
                        'sell_price': sell_price,
                        'pnl': pnl,
                        'pnl_pct': pnl_pct,
                        'is_win': pnl > 0
                    })
                    
                    remaining -= matched_shares
                    buy['shares'] -= matched_shares
                    
                    if buy['shares'] == 0:
                        buy_queue.pop(0)
        
        if not trade_pnl:
            return {'total_trades': len(trade_records)}
        
        pnl_df = pd.DataFrame(trade_pnl)
        
        # 计算胜率
        win_count = (pnl_df['pnl'] > 0).sum()
        loss_count = (pnl_df['pnl'] < 0).sum()
        total_trades = len(pnl_df)
        
        # 计算盈亏比
        avg_win = pnl_df[pnl_df['pnl'] > 0]['pnl'].mean() if win_count > 0 else 0
        avg_loss = abs(pnl_df[pnl_df['pnl'] < 0]['pnl'].mean()) if loss_count > 0 else 0
        profit_factor = avg_win / avg_loss if avg_loss > 0 else 0
        
        # 总盈亏
        total_pnl = pnl_df['pnl'].sum()
        
        return {
            'total_round_trips': total_trades,
            'win_count': win_count,
            'loss_count': loss_count,
            'win_rate': win_count / total_trades if total_trades > 0 else 0,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'profit_factor': profit_factor,
            'total_pnl': total_pnl,
            'avg_pnl': pnl_df['pnl'].mean(),
            'max_win': pnl_df['pnl'].max(),
            'max_loss': pnl_df['pnl'].min(),
            'trade_details': pnl_df
        }