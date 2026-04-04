# -*- coding: utf-8 -*-
"""基准对比"""

from typing import Dict
import pandas as pd
import numpy as np

from utils.logger import get_logger

logger = get_logger('benchmark')


class Benchmark:
    """基准对比（沪深300等）"""
    
    def __init__(self, benchmark_code: str = "000300.SH"):
        self.benchmark_code = benchmark_code
        self.data: pd.DataFrame = None
    
    def load_data(self, start_date: str, end_date: str):
        """加载基准数据
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
        """
        try:
            import akshare as ak
            
            # 沪深300指数
            if self.benchmark_code == "000300.SH":
                df = ak.stock_zh_index_daily(symbol="sh000300")
            else:
                df = ak.stock_zh_index_daily(symbol=self.benchmark_code.lower())
            
            # 过滤日期
            df['date'] = pd.to_datetime(df['date'])
            start = pd.to_datetime(start_date)
            end = pd.to_datetime(end_date)
            
            self.data = df[(df['date'] >= start) & (df['date'] <= end)].copy()
            self.data = self.data.reset_index(drop=True)
            
            logger.info(f"加载基准数据: {len(self.data)}条")
            
        except Exception as e:
            logger.warning(f"加载基准数据失败: {e}")
            self.data = pd.DataFrame()
    
    def get_returns(self) -> pd.Series:
        """获取基准收益率序列
        
        Returns:
            日收益率序列
        """
        if self.data is None or self.data.empty:
            return pd.Series()
        
        returns = self.data['close'].pct_change()
        return returns
    
    def get_cum_returns(self) -> pd.Series:
        """获取累计收益率
        
        Returns:
            累计收益率序列
        """
        returns = self.get_returns()
        return (1 + returns).cumprod() - 1
    
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
        # 简化处理：假设已对齐
        
        strategy_cum = (1 + strategy_returns).cumprod() - 1
        benchmark_cum = (1 + benchmark_returns).cumprod() - 1
        
        return {
            'strategy_total_return': strategy_cum.iloc[-1] if len(strategy_cum) > 0 else 0,
            'benchmark_total_return': benchmark_cum.iloc[-1] if len(benchmark_cum) > 0 else 0,
            'excess_return': (strategy_cum.iloc[-1] if len(strategy_cum) > 0 else 0) - 
                            (benchmark_cum.iloc[-1] if len(benchmark_cum) > 0 else 0),
            'strategy_sharpe': self._calc_sharpe(strategy_returns),
            'benchmark_sharpe': self._calc_sharpe(benchmark_returns),
        }
    
    def _calc_sharpe(self, returns: pd.Series, risk_free: float = 0.03) -> float:
        """计算夏普比率"""
        if returns.std() == 0:
            return 0
        excess = returns - risk_free / 252
        return excess.mean() / excess.std() * np.sqrt(252)