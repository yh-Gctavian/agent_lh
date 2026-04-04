# -*- coding: utf-8 -*-
"""绩效指标计算 - 胜率、盈亏比、夏普、最大回撤等"""

from typing import Dict, List, Optional, Tuple
from datetime import date
import pandas as pd
import numpy as np

from wave_bottom_strategy.utils.logger import get_logger

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
        """计算日收益率"""
        if daily_values.empty or 'total_value' not in daily_values.columns:
            return pd.Series()
        
        values = daily_values['total_value']
        returns = values.pct_change()
        returns.iloc[0] = 0
        
        return returns
    
    def calc_cumulative_return(self, daily_values: pd.DataFrame) -> float:
        """计算累计收益率"""
        if daily_values.empty or 'total_value' not in daily_values.columns:
            return 0.0
        
        start_value = daily_values['total_value'].iloc[0]
        end_value = daily_values['total_value'].iloc[-1]
        
        if start_value == 0:
            return 0.0
        
        return (end_value - start_value) / start_value
    
    def calc_annualized_return(self, daily_values: pd.DataFrame) -> float:
        """计算年化收益率"""
        if daily_values.empty:
            return 0.0
        
        cumulative = self.calc_cumulative_return(daily_values)
        n_days = len(daily_values)
        
        if n_days == 0:
            return 0.0
        
        return (1 + cumulative) ** (252 / n_days) - 1
    
    def calc_volatility(self, daily_values: pd.DataFrame) -> float:
        """计算年化波动率"""
        returns = self.calc_returns(daily_values)
        
        if returns.empty:
            return 0.0
        
        return returns.std() * np.sqrt(252)
    
    def calc_sharpe_ratio(self, daily_values: pd.DataFrame) -> float:
        """计算夏普比率"""
        annualized_return = self.calc_annualized_return(daily_values)
        volatility = self.calc_volatility(daily_values)
        
        if volatility == 0:
            return 0.0
        
        return (annualized_return - self.risk_free_rate) / volatility
    
    def calc_max_drawdown(self, daily_values: pd.DataFrame) -> Dict:
        """计算最大回撤"""
        if daily_values.empty or 'total_value' not in daily_values.columns:
            return {'max_drawdown': 0, 'start_date': None, 'end_date': None}
        
        values = daily_values['total_value']
        cummax = values.cummax()
        drawdown = (values - cummax) / cummax
        
        max_dd = drawdown.min()
        
        end_idx = drawdown.idxmin()
        end_date = daily_values.loc[end_idx, 'date'] if 'date' in daily_values.columns else None
        
        start_idx = values[:end_idx].idxmax()
        start_date = daily_values.loc[start_idx, 'date'] if 'date' in daily_values.columns else None
        
        return {
            'max_drawdown': abs(max_dd),
            'start_date': start_date,
            'end_date': end_date,
            'drawdown_series': drawdown
        }
    
    def calc_calmar_ratio(self, daily_values: pd.DataFrame) -> float:
        """计算卡玛比率"""
        annualized_return = self.calc_annualized_return(daily_values)
        max_dd = self.calc_max_drawdown(daily_values)['max_drawdown']
        
        if max_dd == 0:
            return 0.0
        
        return annualized_return / max_dd
    
    def calc_sortino_ratio(self, daily_values: pd.DataFrame) -> float:
        """计算索提诺比率"""
        returns = self.calc_returns(daily_values)
        
        if returns.empty:
            return 0.0
        
        downside_returns = returns[returns < 0]
        
        if downside_returns.empty:
            return float('inf')
        
        downside_std = downside_returns.std() * np.sqrt(252)
        annualized_return = self.calc_annualized_return(daily_values)
        
        if downside_std == 0:
            return 0.0
        
        return (annualized_return - self.risk_free_rate) / downside_std
    
    def calc_win_rate(self, trade_records: pd.DataFrame) -> Dict:
        """计算胜率"""
        if trade_records.empty:
            return {'win_rate': 0, 'win_count': 0, 'loss_count': 0, 'total_trades': 0}
        
        sells = trade_records[trade_records['direction'] == 'sell'].copy()
        
        if sells.empty:
            return {'win_rate': 0, 'win_count': 0, 'loss_count': 0, 'total_trades': 0}
        
        return {
            'win_rate': 0,
            'win_count': 0,
            'loss_count': 0,
            'total_trades': len(sells)
        }
    
    def generate_report(
        self,
        daily_values: pd.DataFrame,
        trade_records: pd.DataFrame = None,
        benchmark_values: pd.DataFrame = None
    ) -> Dict:
        """生成绩效报告"""
        if daily_values.empty:
            return {}
        
        report = {
            'cumulative_return': self.calc_cumulative_return(daily_values),
            'annualized_return': self.calc_annualized_return(daily_values),
            'volatility': self.calc_volatility(daily_values),
            'max_drawdown': self.calc_max_drawdown(daily_values)['max_drawdown'],
            'max_drawdown_info': self.calc_max_drawdown(daily_values),
            'sharpe_ratio': self.calc_sharpe_ratio(daily_values),
            'calmar_ratio': self.calc_calmar_ratio(daily_values),
            'sortino_ratio': self.calc_sortino_ratio(daily_values),
            'trade_stats': {}
        }
        
        if trade_records is not None and not trade_records.empty:
            report['trade_stats'] = {
                'total_trades': len(trade_records),
                'buy_count': len(trade_records[trade_records['direction'] == 'buy']),
                'sell_count': len(trade_records[trade_records['direction'] == 'sell']),
                'total_commission': trade_records['commission'].sum() if 'commission' in trade_records.columns else 0,
                'total_stamp_duty': trade_records['stamp_duty'].sum() if 'stamp_duty' in trade_records.columns else 0,
                'total_transfer_fee': trade_records['transfer_fee'].sum() if 'transfer_fee' in trade_records.columns else 0
            }
        
        if benchmark_values is not None and not benchmark_values.empty:
            bench_return = self.calc_cumulative_return(benchmark_values)
            report['benchmark'] = {
                'benchmark_return': bench_return,
                'excess_return': report['cumulative_return'] - bench_return
            }
        
        return report


class TradeAnalyzer:
    """交易分析器 - 详细盈亏分析"""
    
    def __init__(self):
        self.trades: List[dict] = []
    
    def analyze_trades(self, trade_records: pd.DataFrame) -> Dict:
        """分析交易记录"""
        if trade_records.empty:
            return {}
        
        buys = trade_records[trade_records['direction'] == 'buy']
        sells = trade_records[trade_records['direction'] == 'sell']
        
        trade_pnl = []
        
        for ts_code in buys['ts_code'].unique():
            stock_buys = buys[buys['ts_code'] == ts_code].sort_values('trade_date')
            stock_sells = sells[sells['ts_code'] == ts_code].sort_values('trade_date')
            
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
        
        win_count = (pnl_df['pnl'] > 0).sum()
        loss_count = (pnl_df['pnl'] < 0).sum()
        total_trades = len(pnl_df)
        
        avg_win = pnl_df[pnl_df['pnl'] > 0]['pnl'].mean() if win_count > 0 else 0
        avg_loss = abs(pnl_df[pnl_df['pnl'] < 0]['pnl'].mean()) if loss_count > 0 else 0
        profit_factor = avg_win / avg_loss if avg_loss > 0 else 0
        
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
            'avg_holding_days': self._calc_avg_holding_days(pnl_df),
            'trade_details': pnl_df
        }
    
    def _calc_avg_holding_days(self, pnl_df: pd.DataFrame) -> float:
        """计算平均持仓天数"""
        if pnl_df.empty:
            return 0
        
        try:
            pnl_df['buy_date'] = pd.to_datetime(pnl_df['buy_date'])
            pnl_df['sell_date'] = pd.to_datetime(pnl_df['sell_date'])
            pnl_df['holding_days'] = (pnl_df['sell_date'] - pnl_df['buy_date']).dt.days
            return pnl_df['holding_days'].mean()
        except:
            return 0