# -*- coding: utf-8 -*-
"""信号生成器"""

import pandas as pd
from typing import List


class SignalGenerator:
    """信号生成器"""
    
    def __init__(self, buy_threshold: float = 70, sell_threshold: float = 30):
        self.buy_threshold = buy_threshold
        self.sell_threshold = sell_threshold
    
    def generate(self, scores: pd.DataFrame, kdj_data: pd.DataFrame) -> pd.DataFrame:
        """生成买卖信号
        
        Args:
            scores: 因子得分
            kdj_data: KDJ数据
            
        Returns:
            包含信号的DataFrame
        """
        signals = scores.copy()
        signals['signal'] = 0
        
        # 买入条件：综合得分>=阈值 且 J值超卖
        buy_mask = (
            (scores['total_score'] >= self.buy_threshold) &
            (kdj_data['j'] < 20)
        )
        signals.loc[buy_mask, 'signal'] = 1
        
        # 卖出条件：综合得分<阈值 或 J值超买
        sell_mask = (
            (scores['total_score'] < self.sell_threshold) |
            (kdj_data['j'] > 80)
        )
        signals.loc[sell_mask, 'signal'] = -1
        
        return signals
    
    def get_buy_list(self, signals: pd.DataFrame) -> List[str]:
        """获取买入股票列表"""
        return signals[signals['signal'] == 1]['ts_code'].tolist()
    
    def get_sell_list(self, signals: pd.DataFrame) -> List[str]:
        """获取卖出股票列表"""
        return signals[signals['signal'] == -1]['ts_code'].tolist()