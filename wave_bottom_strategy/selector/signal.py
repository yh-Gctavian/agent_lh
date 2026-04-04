# -*- coding: utf-8 -*-
"""信号生成器"""

from typing import List
import pandas as pd
import logging

logger = logging.getLogger('signal_generator')


class SignalGenerator:
    """信号生成器"""
    
    def __init__(self, min_score: float = 60.0):
        self.min_score = min_score
    
    def generate(self, scores: pd.DataFrame) -> pd.DataFrame:
        """生成信号"""
        signals = scores.copy()
        signals['signal'] = 0
        signals.loc[signals['total_score'] >= self.min_score, 'signal'] = 1
        return signals
    
    def get_buy_signals(self, signals: pd.DataFrame) -> List[str]:
        """获取买入信号股票"""
        buy_df = signals[signals['signal'] == 1]
        if 'ts_code' in buy_df.columns:
            return buy_df['ts_code'].tolist()
        return []