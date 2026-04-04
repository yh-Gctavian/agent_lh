# -*- coding: utf-8 -*-
"""分层分析"""

from typing import Dict, List, Optional
import pandas as pd
import numpy as np

from utils.logger import get_logger

logger = get_logger('layering_analysis')


class LayeringAnalysis:
    """分层分析
    
    按不同维度分组分析策略表现：
    - 年度
    - 市场环境（牛市/熊市/震荡）
    - 行业
    - 信号强度
    """
    
    def __init__(self, daily_values: pd.DataFrame, trade_records: pd.DataFrame = None):
        self.daily_values = daily_values
        self.trade_records = trade_records
    
    def analyze_by_year(self) -> pd.DataFrame:
        """按年度分层分析
        
        Returns:
            年度收益统计
        """
        if self.daily_values.empty:
            return pd.DataFrame()
        
        df = self.daily_values.copy()
        df['date'] = pd.to_datetime(df['date'])
        df['year'] = df['date'].dt.year
        
        results = []
        
        for year, group in df.groupby('year'):
            if len(group) < 2:
                continue
            
            values = group['total_value']
            returns = values.pct_change()
            
            # 计算峰值和回撤
            peak = values.expanding().max()
            drawdown = (values - peak) / peak
            
            results.append({
                'year': year,
                'start_value': values.iloc[0],
                'end_value': values.iloc[-1],
                'total_return': (values.iloc[-1] - values.iloc[0]) / values.iloc[0],
                'max_drawdown': drawdown.min(),
                'volatility': returns.std() * np.sqrt(252),
                'trade_days': len(group)
            })
        
        return pd.DataFrame(results)
    
    def analyze_by_market(self, benchmark_data: pd.DataFrame = None) -> pd.DataFrame:
        """按市场环境分层
        
        Args:
            benchmark_data: 基准数据
            
        Returns:
            市场环境分析结果
        """
        # 简化实现：按收益率划分市场环境
        if self.daily_values.empty:
            return pd.DataFrame()
        
        df = self.daily_values.copy()
        returns = df['total_value'].pct_change()
        
        # 定义市场环境
        def classify_market(ret):
            if ret > 0.02:
                return 'bull'  # 牛市
            elif ret < -0.02:
                return 'bear'  # 熊市
            else:
                return 'sideways'  # 震荡
        
        df['market'] = returns.apply(classify_market)
        df['date'] = pd.to_datetime(df['date'])
        
        results = []
        for market, group in df.groupby('market'):
            if len(group) < 2:
                continue
            
            values = group['total_value']
            results.append({
                'market': market,
                'days': len(group),
                'avg_return': returns.loc[group.index].mean(),
                'win_rate': len(returns.loc[group.index][returns.loc[group.index] > 0]) / len(group)
            })
        
        return pd.DataFrame(results)
    
    def analyze_by_signal_strength(
        self,
        scores: pd.DataFrame,
        n_groups: int = 5
    ) -> pd.DataFrame:
        """按信号强度分层
        
        Args:
            scores: 因子得分数据
            n_groups: 分组数
            
        Returns:
            信号强度分层结果
        """
        if scores.empty or 'total_score' not in scores.columns:
            return pd.DataFrame()
        
        # 按得分分组
        scores['group'] = pd.qcut(
            scores['total_score'],
            n_groups,
            labels=[f'G{i+1}' for i in range(n_groups)],
            duplicates='drop'
        )
        
        results = []
        for group_name, group_data in scores.groupby('group'):
            results.append({
                'group': group_name,
                'count': len(group_data),
                'avg_score': group_data['total_score'].mean(),
                'min_score': group_data['total_score'].min(),
                'max_score': group_data['total_score'].max()
            })
        
        return pd.DataFrame(results)
    
    def analyze_by_industry(
        self,
        trades: pd.DataFrame,
        industry_map: Dict[str, str] = None
    ) -> pd.DataFrame:
        """按行业分层
        
        Args:
            trades: 交易记录
            industry_map: 股票代码->行业映射
            
        Returns:
            行业分析结果
        """
        if trades.empty:
            return pd.DataFrame()
        
        # 简化：如果没有行业映射，返回空
        if industry_map is None:
            logger.warning("无行业映射数据")
            return pd.DataFrame()
        
        trades['industry'] = trades['symbol'].map(industry_map)
        
        results = []
        for industry, group in trades.groupby('industry'):
            results.append({
                'industry': industry,
                'trade_count': len(group),
                'buy_count': len(group[group['direction'] == 'buy']),
                'sell_count': len(group[group['direction'] == 'sell'])
            })
        
        return pd.DataFrame(results)
    
    def rolling_analysis(self, window: int = 60) -> pd.DataFrame:
        """滚动分析
        
        Args:
            window: 滚动窗口大小
            
        Returns:
            滚动指标
        """
        if self.daily_values.empty:
            return pd.DataFrame()
        
        df = self.daily_values.copy()
        values = df['total_value']
        returns = values.pct_change()
        
        # 滚动收益
        df['rolling_return'] = values.pct_change(window)
        
        # 滚动波动率
        df['rolling_vol'] = returns.rolling(window).std() * np.sqrt(252)
        
        # 滚动夏普
        df['rolling_sharpe'] = returns.rolling(window).mean() / returns.rolling(window).std() * np.sqrt(252)
        
        # 滚动最大回撤
        def rolling_max_dd(series):
            peak = series.expanding().max()
            dd = (series - peak) / peak
            return dd.min()
        
        df['rolling_max_dd'] = values.rolling(window).apply(rolling_max_dd)
        
        return df
    
    def get_summary(self) -> Dict:
        """获取分层分析摘要"""
        yearly = self.analyze_by_year()
        
        if yearly.empty:
            return {}
        
        return {
            'best_year': yearly.loc[yearly['total_return'].idxmax(), 'year'],
            'worst_year': yearly.loc[yearly['total_return'].idxmin(), 'year'],
            'avg_yearly_return': yearly['total_return'].mean(),
            'positive_years': len(yearly[yearly['total_return'] > 0]),
            'negative_years': len(yearly[yearly['total_return'] < 0])
        }