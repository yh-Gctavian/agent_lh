# -*- coding: utf-8 -*-
"""基准对比"""

from typing import Dict, Optional
import pandas as pd
import numpy as np

from data.loader import DataLoader
from utils.logger import get_logger

logger = get_logger('benchmark')


class Benchmark:
    """基准对比
    
    对比策略与沪深300等基准表现
    """
    
    def __init__(self, benchmark_code: str = "000300"):
        self.benchmark_code = benchmark_code
        self.data: pd.DataFrame = None
    
    def load_data(
        self,
        start_date: str,
        end_date: str
    ) -> pd.DataFrame:
        """加载基准数据
        
        Args:
            start_date: 开始日期 (YYYYMMDD)
            end_date: 结束日期 (YYYYMMDD)
            
        Returns:
            基准数据
        """
        try:
            import akshare as ak
            
            # 沪深300指数
            df = ak.stock_zh_index_daily(symbol=f"sh{self.benchmark_code}")
            
            # 过滤日期
            df['trade_date'] = pd.to_datetime(df['date'])
            start = pd.to_datetime(start_date)
            end = pd.to_datetime(end_date)
            
            df = df[(df['trade_date'] >= start) & (df['trade_date'] <= end)]
            
            self.data = df[['trade_date', 'close']].copy()
            self.data.columns = ['trade_date', 'benchmark_close']
            
            logger.info(f"加载基准数据: {len(self.data)}条")
            
            return self.data
            
        except Exception as e:
            logger.error(f"加载基准数据失败: {e}")
            return pd.DataFrame()
    
    def get_returns(self) -> pd.Series:
        """获取基准收益率序列
        
        Returns:
            日收益率序列
        """
        if self.data is None or self.data.empty:
            return pd.Series()
        
        returns = self.data['benchmark_close'].pct_change()
        returns.index = self.data['trade_date']
        
        return returns
    
    def get_cumulative_returns(self) -> pd.Series:
        """获取累计收益率
        
        Returns:
            累计收益率序列
        """
        returns = self.get_returns()
        
        if returns.empty:
            return pd.Series()
        
        cumulative = (1 + returns).cumprod() - 1
        
        return cumulative
    
    def compare(
        self,
        strategy_returns: pd.Series,
        strategy_cumulative: pd.Series = None
    ) -> Dict:
        """对比策略与基准表现
        
        Args:
            strategy_returns: 策略日收益率
            strategy_cumulative: 策略累计收益率
            
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
        
        strategy_aligned = strategy_returns.loc[common_dates]
        benchmark_aligned = benchmark_returns.loc[common_dates]
        
        # 计算超额收益
        excess_returns = strategy_aligned - benchmark_aligned
        
        # 计算指标
        result = {
            'strategy_total_return': (1 + strategy_aligned).prod() - 1,
            'benchmark_total_return': (1 + benchmark_aligned).prod() - 1,
            'excess_return': (1 + strategy_aligned).prod() - (1 + benchmark_aligned).prod(),
            'strategy_sharpe': self._calc_sharpe(strategy_aligned),
            'benchmark_sharpe': self._calc_sharpe(benchmark_aligned),
            'strategy_max_drawdown': self._calc_max_drawdown(strategy_aligned),
            'benchmark_max_drawdown': self._calc_max_drawdown(benchmark_aligned),
            'win_rate': (excess_returns > 0).sum() / len(excess_returns),
            'correlation': strategy_aligned.corr(benchmark_aligned),
        }
        
        return result
    
    def _calc_sharpe(
        self,
        returns: pd.Series,
        risk_free_rate: float = 0.03
    ) -> float:
        """计算夏普比率"""
        excess = returns - risk_free_rate / 252
        if excess.std() == 0:
            return 0.0
        return excess.mean() / excess.std() * np.sqrt(252)
    
    def _calc_max_drawdown(self, returns: pd.Series) -> float:
        """计算最大回撤"""
        cumulative = (1 + returns).cumprod()
        peak = cumulative.expanding(min_periods=1).max()
        drawdown = (cumulative - peak) / peak
        return drawdown.min()
    
    def generate_comparison_report(
        self,
        strategy_history: pd.DataFrame
    ) -> pd.DataFrame:
        """生成对比报告
        
        Args:
            strategy_history: 策略历史记录
            
        Returns:
            对比数据
        """
        if self.data is None or self.data.empty:
            logger.warning("基准数据未加载")
            return pd.DataFrame()
        
        # 对齐日期
        strategy_history['trade_date'] = pd.to_datetime(strategy_history['date'])
        
        merged = pd.merge(
            strategy_history,
            self.data,
            on='trade_date',
            how='left'
        )
        
        # 计算基准收益率
        merged['benchmark_return'] = merged['benchmark_close'].pct_change()
        merged['benchmark_cumulative'] = (1 + merged['benchmark_return'].fillna(0)).cumprod() - 1
        
        # 策略累计收益
        if 'profit_pct' in merged.columns:
            merged['strategy_cumulative'] = merged['profit_pct'] / 100
        
        return merged