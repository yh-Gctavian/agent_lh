# -*- coding: utf-8 -*-
"""股票过滤器"""

from typing import List, Set
import pandas as pd

from utils.logger import get_logger

logger = get_logger('stock_filter')


class StockFilter:
    """股票过滤器
    
    剔除不符合条件的股票（ST、停牌、退市）
    """
    
    def __init__(
        self,
        exclude_st: bool = True,
        exclude_suspended: bool = True,
        exclude_delisted: bool = True
    ):
        self.exclude_st = exclude_st
        self.exclude_suspended = exclude_suspended
        self.exclude_delisted = exclude_delisted
        
        # 缓存
        self._st_stocks: Set[str] = set()
        self._suspended_stocks: Set[str] = set()
        self._delisted_stocks: Set[str] = set()
    
    def load_filter_lists(self):
        """加载过滤列表"""
        try:
            import akshare as ak
            
            # ST股票
            if self.exclude_st:
                df_st = ak.stock_zh_a_st_em()
                self._st_stocks = set(df_st['代码'].tolist())
                logger.info(f"加载ST股票: {len(self._st_stocks)}只")
            
            # 退市股票（从股票基本信息获取）
            if self.exclude_delisted:
                # AKShare退市数据
                logger.info("退市股票过滤已启用")
            
        except Exception as e:
            logger.warning(f"加载过滤列表失败: {e}")
    
    def filter(
        self,
        stock_pool: List[str],
        trade_date: str = None
    ) -> List[str]:
        """过滤股票池
        
        Args:
            stock_pool: 原始股票池
            trade_date: 交易日期
            
        Returns:
            过滤后的股票池
        """
        result = set(stock_pool)
        
        # 剔除ST
        if self.exclude_st and self._st_stocks:
            result = result - self._st_stocks
            logger.info(f"剔除ST后: {len(result)}只")
        
        # 剔除停牌
        if self.exclude_suspended and trade_date:
            suspended = self._get_suspended_stocks(trade_date)
            result = result - suspended
            logger.info(f"剔除停牌后: {len(result)}只")
        
        # 剔除退市
        if self.exclude_delisted and self._delisted_stocks:
            result = result - self._delisted_stocks
            logger.info(f"剔除退市后: {len(result)}只")
        
        return list(result)
    
    def _get_suspended_stocks(self, trade_date: str) -> Set[str]:
        """获取当日停牌股票"""
        try:
            import akshare as ak
            df = ak.stock_tfp_em()
            return set(df['代码'].tolist())
        except Exception as e:
            logger.warning(f"获取停牌股票失败: {e}")
            return set()
    
    def is_valid_stock(
        self,
        symbol: str,
        name: str = None
    ) -> bool:
        """判断股票是否有效
        
        Args:
            symbol: 股票代码
            name: 股票名称
            
        Returns:
            是否有效
        """
        if self.exclude_st:
            if symbol in self._st_stocks:
                return False
            if name and ('ST' in name or '*ST' in name):
                return False
        
        if self.exclude_delisted:
            if symbol in self._delisted_stocks:
                return False
        
        return True
    
    def filter_by_price(
        self,
        stocks_data: pd.DataFrame,
        min_price: float = 2.0,
        max_price: float = 100.0
    ) -> pd.DataFrame:
        """按价格过滤
        
        Args:
            stocks_data: 股票数据
            min_price: 最低价格
            max_price: 最高价格
            
        Returns:
            过滤后的数据
        """
        if 'close' in stocks_data.columns:
            result = stocks_data[
                (stocks_data['close'] >= min_price) &
                (stocks_data['close'] <= max_price)
            ]
            logger.info(f"价格过滤后: {len(result)}条")
            return result
        
        return stocks_data
    
    def filter_by_volume(
        self,
        stocks_data: pd.DataFrame,
        min_volume: float = 0
    ) -> pd.DataFrame:
        """按成交量过滤
        
        Args:
            stocks_data: 股票数据
            min_volume: 最低成交量
            
        Returns:
            过滤后的数据
        """
        if 'volume' in stocks_data.columns:
            result = stocks_data[stocks_data['volume'] > min_volume]
            logger.info(f"成交量过滤后: {len(result)}条")
            return result
        
        return stocks_data