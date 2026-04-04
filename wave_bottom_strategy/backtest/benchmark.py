# -*- coding: utf-8 -*-
"""基准对比"""

from typing import Dict
import pandas as pd
import numpy as np

try:
    import akshare as ak
except ImportError:
    ak = None

from utils.logger import get_logger

logger = get_logger('benchmark')


class Benchmark:
    """基准对比（沪深300等）"""
    
    def __init__(self, benchmark_code: str = "000300"):
        self.benchmark_code = benchmark_code
        self.data: pd.DataFrame = None
    
    def load_data(self, start_date: str, end_date: str) -> pd.DataFrame:
        """加载基准数据
        
        Args:
            start_date: 开始日期 (YYYYMMDD)
            end_date: 结束日期 (YYYYMMDD)
        """
        if ak:
            try:
                # 沪深300指数
                df = ak.stock_zh_index_daily(symbol=f"sh{self.benchmark_code}")
                df = df[(df['date'] >= start_date) & (df['date'] <= end_date)]
                df = df.rename(columns={'date': 'trade_date', 'close': 'benchmark_close'})
                self.data = df[['trade_date', 'benchmark_close']]
                logger.info(f"基准数据加载完成: {len(self.data)}条")
                return self.data
            except Exception as e:
                logger.warning(f"基准数据加载失败: {e}")
        
        return pd.DataFrame()
    
    def get_returns(self) -> pd.Series:
        """获取基准收益率序列"""
        if self.data is None or self.data.empty:
            return pd.Series()
        
        returns = self.data['benchmark_close'].pct_change()
        return returns.dropna()
    
    def compare(self, strategy_returns: pd.Series) -> Dict:
        """对比策略与基准表现
        
        Args:
            strategy_returns: 策略日收益率
            
        Returns:
            对比结果
        """
        benchmark_returns = self.get_returns()
        
        if benchmark_returns.empty or strategy_returns.empty:
            return {}
        
        # 对齐日期
        common_dates = strategy_returns.index.intersection(benchmark_returns.index)
        
        if len(common_dates) == 0:
            return {}
        
        strat = strategy_returns.loc[common_dates]
        bench = benchmark_returns.loc[common_dates]
        
        # 计算超额收益
        excess_returns = strat - bench
        
        return {
            'strategy_total_return': (1 + strat).prod() - 1,
            'benchmark_total_return': (1 + bench).prod() - 1,
            'excess_return': (1 + excess_returns).prod() - 1,
            'strategy_sharpe': strat.mean() / strat.std() * np.sqrt(252) if strat.std() > 0 else 0,
            'benchmark_sharpe': bench.mean() / bench.std() * np.sqrt(252) if bench.std() > 0 else 0,
        }