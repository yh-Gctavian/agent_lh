# -*- coding: utf-8 -*-
"""选股引擎核心"""

from typing import List, Dict, Optional
from datetime import date
import pandas as pd

from .scorer import FactorScorer
from .filter import StockFilter
from .signal import SignalGenerator
from data.loader import DataLoader
from data.processor import DataProcessor
from utils.logger import get_logger

logger = get_logger('selector_engine')


class SelectorEngine:
    """选股引擎
    
    整合数据加载、因子计算、打分、筛选、信号生成
    """
    
    def __init__(
        self,
        scorer: FactorScorer = None,
        stock_filter: StockFilter = None,
        signal_generator: SignalGenerator = None,
        data_loader: DataLoader = None
    ):
        self.scorer = scorer or FactorScorer()
        self.stock_filter = stock_filter or StockFilter()
        self.signal_generator = signal_generator or SignalGenerator()
        self.data_loader = data_loader or DataLoader()
        self.data_processor = DataProcessor()
        
        # 加载过滤列表
        self.stock_filter.load_filter_lists()
        
        logger.info("选股引擎初始化完成")
    
    def run(
        self,
        trade_date: date,
        stock_pool: List[str] = None,
        top_n: int = 10,
        min_score: float = 60.0
    ) -> pd.DataFrame:
        """执行选股
        
        Args:
            trade_date: 交易日期
            stock_pool: 股票池，None则使用沪深300
            top_n: 返回数量
            min_score: 最低得分
            
        Returns:
            选股结果
        """
        logger.info(f"选股执行: {trade_date}")
        
        # 1. 获取股票池
        if stock_pool is None:
            stock_pool = self.data_loader.load_stock_pool('hs300')
            logger.info(f"使用沪深300股票池: {len(stock_pool)}只")
        
        # 2. 过滤股票池
        filtered_pool = self.stock_filter.filter(
            stock_pool,
            trade_date=str(trade_date)
        )
        logger.info(f"过滤后股票池: {len(filtered_pool)}只")
        
        # 3. 批量评分
        all_scores = self._batch_score(filtered_pool, trade_date)
        
        # 4. 生成信号
        signals = self.signal_generator.generate(all_scores)
        
        # 5. 获取Top N
        top_stocks = self.scorer.get_top_stocks(signals, top_n, min_score)
        
        logger.info(f"选股完成: {len(top_stocks)}只")
        
        return top_stocks
    
    def _batch_score(
        self,
        symbols: List[str],
        trade_date: date
    ) -> pd.DataFrame:
        """批量评分
        
        Args:
            symbols: 股票列表
            trade_date: 交易日期
            
        Returns:
            所有股票评分结果
        """
        results = []
        
        for i, symbol in enumerate(symbols):
            logger.debug(f"评分进度: {i+1}/{len(symbols)} - {symbol}")
            
            try:
                # 加载该股票数据
                df = self.data_loader.load_daily_data(
                    symbol=symbol,
                    start_date='20200101',
                    end_date=str(trade_date).replace('-', ''),
                    adjust='qfq'
                )
                
                if df.empty:
                    continue
                
                # 数据预处理
                df = self.data_processor.process_all(df, symbol)
                
                # 截取最近数据（避免全量计算）
                recent_df = df.tail(100)
                
                # 评分
                scores = self.scorer.score_stock(recent_df)
                
                # 取最新一天的得分
                latest = scores.iloc[-1].copy()
                latest['ts_code'] = symbol
                latest['trade_date'] = trade_date
                
                results.append(latest)
                
            except Exception as e:
                logger.warning(f"{symbol} 评分失败: {e}")
        
        return pd.DataFrame(results)
    
    def run_single(
        self,
        symbol: str,
        data: pd.DataFrame = None
    ) -> pd.DataFrame:
        """对单只股票选股评分
        
        Args:
            symbol: 股票代码
            data: 日K线数据（可选，不提供则自动加载）
            
        Returns:
            评分结果
        """
        if data is None:
            data = self.data_loader.load_daily_data(
                symbol=symbol,
                start_date='20200101',
                end_date='20251231',
                adjust='qfq'
            )
        
        if data.empty:
            logger.warning(f"{symbol} 无数据")
            return pd.DataFrame()
        
        # 数据预处理
        data = self.data_processor.process_all(data, symbol)
        
        # 评分
        scores = self.scorer.score_stock(data)
        
        # 生成信号
        signals = self.signal_generator.generate(scores)
        
        return signals
    
    def get_buy_candidates(
        self,
        trade_date: date,
        stock_pool: List[str] = None,
        top_n: int = 10
    ) -> List[str]:
        """获取买入候选
        
        Args:
            trade_date: 交易日期
            stock_pool: 股票池
            top_n: 数量
            
        Returns:
            股票代码列表
        """
        result = self.run(trade_date, stock_pool, top_n)
        
        if 'ts_code' in result.columns:
            return result['ts_code'].tolist()
        
        return []
    
    def get_stock_rank(
        self,
        stock_pool: List[str],
        trade_date: date
    ) -> pd.DataFrame:
        """获取股票排名
        
        Args:
            stock_pool: 股票池
            trade_date: 交易日期
            
        Returns:
            排名结果（按总分排序）
        """
        all_scores = self._batch_score(stock_pool, trade_date)
        
        # 按总分排序
        ranked = all_scores.sort_values('total_score', ascending=False)
        ranked['rank'] = range(1, len(ranked) + 1)
        
        return ranked