# -*- coding: utf-8 -*-
"""信号生成器"""

from typing import List
import pandas as pd


class SignalGenerator:
    """信号生成器
    
    根据因子得分和抄底条件生成买卖信号
    """
    
    def __init__(
        self,
        min_score: float = 60.0,
        buy_threshold: float = 20.0  # KDJ低于20视为超卖
    ):
        self.min_score = min_score
        self.buy_threshold = buy_threshold
    
    def generate(
        self,
        scores: pd.DataFrame,
        kdj_values: pd.DataFrame
    ) -> pd.DataFrame:
        """生成买卖信号
        
        Args:
            scores: 因子得分
            kdj_values: KDJ值（用于抄底判断）
            
        Returns:
            包含信号的结果
        """
        signals = scores.copy()
        
        # 抄底条件：总分 >= min_score 且 KDJ超卖
        signals['signal'] = 0
        signals.loc[
            (signals['total_score'] >= self.min_score) &
            (kdj_values['j'] < self.buy_threshold),
            'signal'
        ] = 1  # 买入信号
        
        return signals
    
    def get_buy_signals(self, signals: pd.DataFrame) -> List[str]:
        """获取买入信号股票
        
        Args:
            signals: 信号结果
            
        Returns:
            买入股票代码列表
        """
        return signals[signals['signal'] == 1]['ts_code'].tolist()