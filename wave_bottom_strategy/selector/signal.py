# -*- coding: utf-8 -*-
"""信号生成器"""

from typing import List, Dict
import pandas as pd

from utils.logger import get_logger

logger = get_logger('signal_generator')


class SignalGenerator:
    """信号生成器
    
    根据因子得分和抄底条件生成买卖信号
    """
    
    def __init__(
        self,
        min_score: float = 60.0,
        kdj_threshold: float = 20.0,  # J值阈值
        buy_signal_threshold: float = 70.0  # 总分阈值
    ):
        self.min_score = min_score
        self.kdj_threshold = kdj_threshold
        self.buy_signal_threshold = buy_signal_threshold
    
    def generate(
        self,
        scores: pd.DataFrame,
        kdj_data: pd.DataFrame = None
    ) -> pd.DataFrame:
        """生成买卖信号
        
        Args:
            scores: 因子得分
            kdj_data: KDJ数据（用于抄底判断）
            
        Returns:
            包含信号的结果
        """
        signals = scores.copy()
        
        # 初始化信号列
        signals['signal'] = 0  # 0=持有, 1=买入, -1=卖出
        
        # 买入条件：总分 >= 阈值
        buy_condition = signals['total_score'] >= self.buy_signal_threshold
        
        # 如果有KDJ数据，加强抄底判断
        if kdj_data is not None and 'j' in kdj_data.columns:
            # J值低于阈值（超卖）加分
            kdj_oversold = kdj_data['j'] < self.kdj_threshold
            buy_condition = buy_condition & kdj_oversold.reindex(signals.index, method='ffill').fillna(False)
        
        signals.loc[buy_condition, 'signal'] = 1
        
        logger.info(f"生成信号: {len(signals[signals['signal'] == 1])}个买入")
        
        return signals
    
    def generate_with_factors(
        self,
        scores: pd.DataFrame,
        factor_results: Dict[str, pd.DataFrame]
    ) -> pd.DataFrame:
        """基于多因子数据生成信号
        
        Args:
            scores: 得分结果
            factor_results: 各因子计算结果
            
        Returns:
            信号结果
        """
        signals = scores.copy()
        signals['signal'] = 0
        
        # 抄底信号组合判断
        buy_signals = pd.Series(False, index=signals.index)
        
        # KDJ超卖
        if 'KDJFactor' in factor_results:
            kdj = factor_results['KDJFactor']
            if 'j' in kdj.columns:
                buy_signals |= (kdj['j'] < 20)
        
        # RSI超卖
        if 'RSIFactor' in factor_results:
            rsi = factor_results['RSIFactor']
            if 'rsi' in rsi.columns:
                buy_signals |= (rsi['rsi'] < 30)
        
        # 布林带下轨
        if 'BollingerFactor' in factor_results:
            bb = factor_results['BollingerFactor']
            if 'bb_pos' in bb.columns:
                buy_signals |= (bb['bb_pos'] < 10)
        
        # 总分达标
        score_ok = signals['total_score'] >= self.buy_signal_threshold
        
        # 综合信号：得分达标 + 至少一个超卖信号
        signals.loc[score_ok & buy_signals.reindex(signals.index, method='ffill').fillna(False), 'signal'] = 1
        
        return signals
    
    def get_buy_signals(self, signals: pd.DataFrame) -> List[str]:
        """获取买入信号股票
        
        Args:
            signals: 信号结果
            
        Returns:
            买入股票代码列表
        """
        buy_df = signals[signals['signal'] == 1]
        if 'ts_code' in buy_df.columns:
            return buy_df['ts_code'].tolist()
        return []
    
    def get_sell_signals(self, signals: pd.DataFrame) -> List[str]:
        """获取卖出信号股票
        
        Args:
            signals: 信号结果
            
        Returns:
            卖出股票代码列表
        """
        sell_df = signals[signals['signal'] == -1]
        if 'ts_code' in sell_df.columns:
            return sell_df['ts_code'].tolist()
        return []
    
    def generate_sell_signal(
        self,
        scores: pd.DataFrame,
        kdj_data: pd.DataFrame = None,
        sell_threshold: float = 80.0  # J值超买阈值
    ) -> pd.DataFrame:
        """生成卖出信号
        
        Args:
            scores: 得分结果
            kdj_data: KDJ数据
            sell_threshold: 卖出阈值
            
        Returns:
            信号结果
        """
        signals = scores.copy()
        signals['signal'] = 0
        
        # 卖出条件：总分低 或 KDJ超买
        sell_condition = signals['total_score'] < 30
        
        if kdj_data is not None and 'j' in kdj_data.columns:
            kdj_overbought = kdj_data['j'] > sell_threshold
            sell_condition |= kdj_overbought.reindex(signals.index, method='ffill').fillna(False)
        
        signals.loc[sell_condition, 'signal'] = -1
        
        return signals