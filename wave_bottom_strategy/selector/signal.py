# -*- coding: utf-8 -*-
"""信号生成?""

from typing import List
import pandas as pd

from ..utils.logger import get_logger

logger = get_logger('signal_generator')


class SignalGenerator:
    """信号生成?
    
    根据因子得分生成买入/卖出信号
    """
    
    def __init__(
        self,
        buy_threshold: float = 70.0,  # 买入�?
        sell_threshold: float = 30.0,  # 卖出�?
        kdj_buy_threshold: float = 20.0  # KDJ超卖�?
    ):
        self.buy_threshold = buy_threshold
        self.sell_threshold = sell_threshold
        self.kdj_buy_threshold = kdj_buy_threshold
    
    def generate(
        self,
        scores: pd.DataFrame,
        kdj_data: pd.DataFrame = None
    ) -> pd.DataFrame:
        """生成信号
        
        Args:
            scores: 因子得分
            kdj_data: KDJ数据（用于超卖判断）
            
        Returns:
            信号结果
        """
        signals = scores.copy()
        signals['signal'] = 0  # 默认持有
        
        # 买入信号：综合得?>= buy_threshold
        signals.loc[signals['total_score'] >= self.buy_threshold, 'signal'] = 1
        
        # 强买入：综合得分高且KDJ超卖
        if kdj_data is not None:
            strong_buy = (
                (signals['total_score'] >= self.buy_threshold) &
                (kdj_data['j'] < self.kdj_buy_threshold)
            )
            signals.loc[strong_buy, 'signal'] = 2  # 强买?
        
        # 卖出信号：综合得?< sell_threshold
        signals.loc[signals['total_score'] < self.sell_threshold, 'signal'] = -1
        
        return signals
    
    def get_buy_signals(self, signals: pd.DataFrame) -> List[str]:
        """获取买入信号股票"""
        return signals[signals['signal'] > 0]['symbol'].tolist()
    
    def get_sell_signals(self, signals: pd.DataFrame) -> List[str]:
        """获取卖出信号股票"""
        return signals[signals['signal'] < 0]['symbol'].tolist()
