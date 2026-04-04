# -*- coding: utf-8 -*-
"""基准对比"""

from typing import Dict
import pandas as pd


class Benchmark:
    """基准对比（沪深300）"""
    
    def __init__(self, benchmark_code: str = "000300"):
        self.benchmark_code = benchmark_code
        self.data: pd.DataFrame = None
    
    def load_data(self, start_date: str, end_date: str) -> pd.DataFrame:
        """加载基准数据"""
        try:
            import akshare as ak
            df = ak.stock_zh_index_daily(symbol=f"sh{self.benchmark_code}")
            df = df.rename(columns={'date': 'trade_date', 'close': 'benchmark_close'})
            df['trade_date'] = pd.to_datetime(df['trade_date'])
            df = df[(df['trade_date'] >= start_date) & (df['trade_date'] <= end_date)]
            df['benchmark_return'] = df['benchmark_close'].pct_change()
            self.data = df
            return df
        except Exception as e:
            print(f"基准数据加载失败: {e}")
            return pd.DataFrame()
    
    def get_returns(self) -> pd.Series:
        """获取基准收益率"""
        if self.data is not None:
            return self.data['benchmark_return']
        return pd.Series()
    
    def compare(self, strategy_returns: pd.Series) -> Dict:
        """对比策略与基准"""
        if self.data is None:
            return {}
        
        benchmark_returns = self.get_returns()
        
        # 计算超额收益
        excess_returns = strategy_returns - benchmark_returns
        
        return {
            'benchmark_total_return': (1 + benchmark_returns).prod() - 1,
            'strategy_total_return': (1 + strategy_returns).prod() - 1,
            'excess_return': (1 + excess_returns).prod() - 1,
            'benchmark_sharpe': benchmark_returns.mean() / benchmark_returns.std() * (252**0.5),
            'strategy_sharpe': strategy_returns.mean() / strategy_returns.std() * (252**0.5)
        }