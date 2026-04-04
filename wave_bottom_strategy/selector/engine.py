# -*- coding: utf-8 -*-
"""选股引擎"""

from typing import List, Dict
from datetime import date
import pandas as pd

from .filter import StockFilter
from .scorer import FactorScorer
from .signal import SignalGenerator
from wave_bottom_strategy.data.loader import DataLoader
from wave_bottom_strategy.utils.logger import get_logger

logger = get_logger('selector_engine')


class SelectorEngine:
    """选股引擎
    
    执行完整的选股流程
    """
    
    def __init__(
        self,
        data_loader: DataLoader = None,
        min_score: float = 60.0,
        max_positions: int = 10
    ):
        self.data_loader = data_loader or DataLoader()
        self.stock_filter = StockFilter()
        self.scorer = FactorScorer()
        self.signal_gen = SignalGenerator()
        
        self.min_score = min_score
        self.max_positions = max_positions
    
    def run(
        self,
        stock_pool: List[str],
        trade_date: str,
        start_date: str = None
    ) -> pd.DataFrame:
        """执行选股
        
        Args:
            stock_pool: 股票?
            trade_date: 交易日期
            start_date: 数据开始日?
            
        Returns:
            选股结果
        """
        logger.info(f"选股执行: {trade_date}, 股票池{len(stock_pool)}?)
        
        # 1. 过滤股票?
        filtered_pool = self.stock_filter.filter(stock_pool)
        
        # 2. 计算各股票因子得?
        if not start_date:
            # 默认?0天历史数据用于因子计?
            start_date = self._get_start_date(trade_date, 60)
        
        scores_dict = {}
        kdj_dict = {}
        
        for symbol in filtered_pool:
            try:
                data = self.data_loader.load_daily_data(
                    symbol, start_date, trade_date
                )
                if data.empty or len(data) < 30:
                    continue
                
                # 计算得分
                scores = self.scorer.calculate_scores(data)
                scores_dict[symbol] = scores
                
                # 计算KDJ（用于超卖判断）
                kdj_data = self.scorer.factors['kdj'].calculate(data)
                kdj_dict[symbol] = kdj_data
                
            except Exception as e:
                logger.warning(f"处理{symbol}失败: {e}")
        
        # 3. 排序获取Top股票
        rankings = self.scorer.rank_stocks(scores_dict, trade_date, self.max_positions)
        
        # 4. 生成信号
        if not rankings.empty:
            rankings['signal'] = rankings['total_score'].apply(
                lambda x: 1 if x >= self.min_score else 0
            )
        
        logger.info(f"选股完成: {len(rankings)}只?)
        return rankings
    
    def _get_start_date(self, end_date: str, days: int) -> str:
        """计算开始日?""
        from datetime import datetime, timedelta
        end_dt = datetime.strptime(end_date.replace('-', ''), '%Y%m%d')
        start_dt = end_dt - timedelta(days=days * 2)  # 多取一些确保有足够交易?
        return start_dt.strftime('%Y%m%d')
    
    def select_top_stocks(
        self,
        result: pd.DataFrame,
        top_n: int = 5
    ) -> List[str]:
        """获取得分最高的N只股?""
        if result.empty:
            return []
        return result.head(top_n)['symbol'].tolist()
