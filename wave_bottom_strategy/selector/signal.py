# -*- coding: utf-8 -*-
"""Signal generator module"""

import pandas as pd


class SignalGenerator:
    """Signal generator - Generate buy/sell signals based on factor scores"""
    
    def __init__(self, buy_threshold: float = 70.0):
        self.buy_threshold = buy_threshold
    
    def generate(self, scores: pd.DataFrame) -> pd.DataFrame:
        """Generate buy/sell signals"""
        signals = scores.copy()
        signals['signal'] = 0
        signals.loc[signals['total_score'] >= self.buy_threshold, 'signal'] = 1
        return signals