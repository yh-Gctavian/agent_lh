# -*- coding: utf-8 -*-
"""选股引擎"""

from typing import List, Dict, Any
from datetime import date
import pandas as pd

from .scorer import FactorScorer
from .filter import StockFilter
from .signal import SignalGenerator


class SelectorEngine:
    """选股引擎"""
    
    def __init__(
        self,
        scorer: FactorScorer,
        stock_filter: StockFilter,
        signal_generator: SignalGenerator
    ):
        self.scorer = scorer
        self.stock_filter = stock_filter
        self.signal_generator = signal_generator
    
    def run(
        self,
        trade_date: date,
        stock_pool: List[str] = None
    ) -> pd.DataFrame:
        """执行选股
        
        Args:
            trade_date: 交易日期
            stock_pool: 股票池，None则使用默认
            
        Returns:
            选股结果，包含股票代码、分数、信号等
        """
        # TODO: 实现选股逻辑
        # 1. 获取股票池
        # 2. 过滤（剔除ST、停牌、退市）
        # 3. 计算各因子得分
        # 4. 加权合成总分
        # 5. 生成信号
        raise NotImplementedError
    
    def get_top_stocks(
        self,
        result: pd.DataFrame,
        top_n: int = 10
    ) -> List[str]:
        """获取得分最高的N只股票
        
        Args:
            result: 选股结果
            top_n: 返回数量
            
        Returns:
            股票代码列表
        """
        # TODO: 实现排序取Top N逻辑
        raise NotImplementedError