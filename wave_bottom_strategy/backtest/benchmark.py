# -*- coding: utf-8 -*-
"""基准对比"""

from typing import Dict
import pandas as pd
import numpy as np

from utils.logger import get_logger

logger = get_logger('benchmark')


class Benchmark:
    """基准对比（沪深300等）"""
    
    def __init__(self, benchmark_code: str = "000300"):
        self.benchmark_code = benchmark_code
        self.data: pd.DataFrame = None
    
    def load_data(self, start_date: str, end_date: str):
        """加载基准数据"""
        try:
            import akshare as ak
            # 沪深300指数
            df = ak.stock_zh_index_daily(symbol=f"sh{self.benchmark_code}")
            df = df[(df['date'] >= start_date) & (df['date'] <= end_date)]
            self.data = df
            logger.info(f"基准数据加载: {len(df)}条")
        except Exception as e:
            logger.warning(f"基准数据加载失败: {e}")
    
    def get_returns(self) -> pd.Series:
        """获取收益率"""
        if self.data is None or self.data.empty:
            return pd.Series()
        return self.data['close'].pct_change()
    
    def compare(self, strategy_returns: pd.Series) -> Dict:
        """对比策略与基准"""
        benchmark_returns = self.get_returns()
        
        if benchmark_returns.empty:
            return {}
        
        # 对齐日期
        strategy_cum = (1 + strategy_returns.fillna(0)).cumprod()
        benchmark_cum = (1 + benchmark_returns.fillna(0)).cumprod()
        
        return {
            'strategy_return': strategy_cum.iloc[-1] - 1 if len(strategy_cum) > 0 else 0,
            'benchmark_return': benchmark_cum.iloc[-1] - 1 if len(benchmark_cum) > 0 else 0,
            'excess_return': (strategy_cum.iloc[-1] - 1) - (benchmark_cum.iloc[-1] - 1) if len(strategy_cum) > 0 and len(benchmark_cum) > 0 else 0
        }