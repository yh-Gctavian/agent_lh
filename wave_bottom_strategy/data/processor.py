# -*- coding: utf-8 -*-
"""数据预处理器"""

from typing import Optional, List, Set
import pandas as pd
from pathlib import Path

from utils.logger import get_logger

logger = get_logger('data_processor')


class DataProcessor:
    """数据预处理器
    
    处理复权、停牌、退市、ST标记等
    """
    
    # ST股票标识关键字
    ST_KEYWORDS = ['ST', '*ST', 'SST', 'S*ST']
    
    def __init__(self):
        self.st_stocks: Set[str] = set()
        self.suspended_dates: dict = {}
        self.delisted_stocks: Set[str] = set()
    
    def load_st_stocks(self) -> Set[str]:
        """加载ST股票列表
        
        Returns:
            ST股票代码集合
        """
        try:
            import akshare as ak
            df = ak.stock_zh_a_st_em()
            self.st_stocks = set(df['代码'].tolist())
            logger.info(f"加载ST股票: {len(self.st_stocks)}只")
            return self.st_stocks
        except Exception as e:
            logger.warning(f"加载ST股票失败: {e}")
            return set()
    
    def load_delisted_stocks(self) -> Set[str]:
        """加载退市股票列表
        
        Returns:
            退市股票代码集合
        """
        try:
            import akshare as ak
            df = ak.stock_zh_a_hist_min_em(symbol="退市", adjust='')
            if not df.empty:
                self.delisted_stocks = set(df['代码'].tolist())
            logger.info(f"加载退市股票: {len(self.delisted_stocks)}只")
            return self.delisted_stocks
        except Exception as e:
            logger.warning(f"加载退市股票失败: {e}")
            return set()
    
    def is_st_stock(self, symbol: str, name: str = None) -> bool:
        """判断是否为ST股票
        
        Args:
            symbol: 股票代码
            name: 股票名称（可选）
            
        Returns:
            是否为ST股票
        """
        if symbol in self.st_stocks:
            return True
        
        if name:
            for keyword in self.ST_KEYWORDS:
                if keyword in name:
                    return True
        
        return False
    
    def filter_stocks(
        self,
        symbols: List[str],
        exclude_st: bool = True,
        exclude_delisted: bool = True,
        exclude_suspended: bool = False,
        trade_date: str = None
    ) -> List[str]:
        """过滤股票池
        
        Args:
            symbols: 原始股票列表
            exclude_st: 是否剔除ST
            exclude_delisted: 是否剔除退市
            exclude_suspended: 是否剔除停牌
            trade_date: 交易日期
            
        Returns:
            过滤后的股票列表
        """
        result = symbols.copy()
        
        if exclude_st:
            self.load_st_stocks()
            result = [s for s in result if s not in self.st_stocks]
            logger.info(f"剔除ST后: {len(result)}只")
        
        if exclude_delisted:
            self.load_delisted_stocks()
            result = [s for s in result if s not in self.delisted_stocks]
            logger.info(f"剔除退市后: {len(result)}只")
        
        if exclude_suspended and trade_date:
            result = self._filter_suspended(result, trade_date)
        
        return result
    
    def _filter_suspended(self, symbols: List[str], trade_date: str) -> List[str]:
        """剔除停牌股票"""
        try:
            import akshare as ak
            df = ak.stock_tfp_em()
            suspended = set(df['代码'].tolist())
            result = [s for s in symbols if s not in suspended]
            logger.info(f"剔除停牌后: {len(result)}只")
            return result
        except Exception as e:
            logger.warning(f"停牌过滤失败: {e}")
            return symbols
    
    def mark_suspended(self, df: pd.DataFrame, symbol: str) -> pd.DataFrame:
        """标记停牌日期"""
        df['is_suspended'] = False
        df.loc[(df['volume'] == 0) | (df['amount'] == 0), 'is_suspended'] = True
        return df
    
    def mark_st_status(self, df: pd.DataFrame, symbol: str, name: str = None) -> pd.DataFrame:
        """标记ST状态"""
        df['is_st'] = self.is_st_stock(symbol, name)
        return df
    
    def validate_data(self, df: pd.DataFrame, symbol: str) -> pd.DataFrame:
        """验证数据完整性"""
        if df.empty:
            return df
        
        df = df.dropna(subset=['open', 'high', 'low', 'close', 'volume'])
        df = df[df['high'] >= df['low']]
        df = df[df['high'] >= df['open']]
        df = df[df['high'] >= df['close']]
        df = df[df['low'] <= df['open']]
        df = df[df['low'] <= df['close']]
        df = df[df['volume'] >= 0]
        
        logger.info(f"{symbol} 数据验证完成: {len(df)}条")
        return df
    
    def process_all(self, df: pd.DataFrame, symbol: str, name: str = None) -> pd.DataFrame:
        """执行全部预处理"""
        df = self.validate_data(df, symbol)
        df = self.mark_suspended(df, symbol)
        df = self.mark_st_status(df, symbol, name)
        return df