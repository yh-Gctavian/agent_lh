# -*- coding: utf-8 -*-
"""数据加载器 - AKShare实现"""

from typing import Optional, List, Dict
from pathlib import Path
import pandas as pd
import akshare as ak
from datetime import datetime
import time
import json
import sys

# 支持两种导入方式
try:
    from wave_bottom_strategy.utils.logger import get_logger
except ImportError:
    from utils.logger import get_logger

logger = get_logger('data_loader')


class DataLoaderError(Exception):
    """数据加载器异常基类"""
    pass


class NetworkError(DataLoaderError):
    """网络请求异常"""
    pass


class DataNotFoundError(DataLoaderError):
    """数据未找到异常"""
    pass


class DataLoader:
    """数据加载器 - 基于AKShare"""
    
    MAX_RETRIES = 3
    RETRY_DELAY = 1.0
    
    def __init__(self, cache_dir: Path = None):
        self.cache_dir = cache_dir or Path('data/cache')
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def _retry_request(self, func, *args, **kwargs):
        """网络请求重试包装"""
        last_error = None
        
        for attempt in range(self.MAX_RETRIES):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_error = e
                error_msg = str(e)
                
                is_network_error = any(keyword in error_msg.lower() for keyword in [
                    'connection', 'timeout', 'network', 'proxy', 'http', 'ssl'
                ])
                
                if is_network_error and attempt < self.MAX_RETRIES - 1:
                    logger.warning(f"网络请求失败(尝试 {attempt + 1}/{self.MAX_RETRIES}): {e}")
                    time.sleep(self.RETRY_DELAY * (attempt + 1))
                else:
                    raise
        
        raise NetworkError(f"网络请求失败，已重试{self.MAX_RETRIES}次: {last_error}")
    
    def load_daily_data(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
        adjust: str = 'qfq',
        use_cache: bool = True
    ) -> pd.DataFrame:
        """加载日K线数据"""
        logger.info(f"加载日K线: {symbol}, {start_date}-{end_date}")
        
        try:
            df = self._retry_request(
                ak.stock_zh_a_hist,
                symbol=symbol,
                period='daily',
                start_date=start_date,
                end_date=end_date,
                adjust=adjust
            )
            
            if df is None or df.empty:
                raise DataNotFoundError(f"股票数据不存在: {symbol}")
            
            df = self._standardize_columns(df)
            df['ts_code'] = f"{symbol}.SZ" if symbol.startswith(('0', '3')) else f"{symbol}.SH"
            
            return df
            
        except Exception as e:
            logger.error(f"加载日K线失败: {symbol}, {e}")
            raise
    
    def load_stock_pool(self, pool_name: str) -> List[str]:
        """加载股票池"""
        logger.info(f"加载股票池: {pool_name}")
        
        try:
            if pool_name == 'hs300':
                df = self._retry_request(ak.index_stock_cons_weight_csindex, symbol='000300')
                codes = self._extract_stock_codes(df)
            elif pool_name == 'zz500':
                df = self._retry_request(ak.index_stock_cons_weight_csindex, symbol='000905')
                codes = self._extract_stock_codes(df)
            elif pool_name == 'all_a':
                df = self._retry_request(ak.stock_info_a_code_name)
                codes = df['code'].tolist()
            else:
                raise ValueError(f"未知股票池: {pool_name}")
            
            logger.info(f"股票池加载成功: {pool_name}, {len(codes)}只股票")
            return codes
                
        except Exception as e:
            logger.error(f"加载股票池失败: {pool_name}, {e}")
            raise
    
    def _extract_stock_codes(self, df: pd.DataFrame) -> List[str]:
        """从指数成分股DataFrame中提取股票代码"""
        possible_columns = ['成分券代码', '成分股代码', 'code', '股票代码', 'symbol']
        
        for col in possible_columns:
            if col in df.columns:
                return df[col].tolist()
        
        raise KeyError(f"无法找到股票代码列，可用列：{df.columns.tolist()}")
    
    def load_stock_basic(self) -> pd.DataFrame:
        """加载股票基本信息"""
        try:
            df = self._retry_request(ak.stock_info_a_code_name)
            
            result = pd.DataFrame()
            result['symbol'] = df['code']
            result['name'] = df['name']
            result['ts_code'] = result['symbol'].apply(
                lambda x: f"{x}.SZ" if x.startswith(('0', '3')) else f"{x}.SH"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"加载股票基本信息失败: {e}")
            raise
    
    def load_trade_calendar(self, start_date: str, end_date: str) -> List[str]:
        """加载交易日历"""
        try:
            df = self._retry_request(ak.tool_trade_date_hist_sina)
            df['trade_date'] = pd.to_datetime(df['trade_date'], format='mixed').dt.strftime('%Y%m%d')
            df = df[(df['trade_date'] >= start_date) & (df['trade_date'] <= end_date)]
            return df['trade_date'].tolist()
            
        except Exception as e:
            logger.error(f"加载交易日历失败: {e}")
            raise
    
    def _standardize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """标准化列名"""
        column_map = {
            '日期': 'trade_date',
            '开盘': 'open',
            '收盘': 'close',
            '最高': 'high',
            '最低': 'low',
            '成交量': 'volume',
            '成交额': 'amount',
            '振幅': 'amplitude',
            '涨跌幅': 'pct_change',
            '涨跌额': 'change',
            '换手率': 'turn'
        }
        
        df = df.rename(columns=column_map)
        
        if 'trade_date' in df.columns:
            df['trade_date'] = pd.to_datetime(df['trade_date'])
        
        return df
    
    def batch_load_daily_data(
        self,
        symbols: List[str],
        start_date: str,
        end_date: str,
        adjust: str = 'qfq'
    ) -> Dict[str, pd.DataFrame]:
        """批量加载日K线数据"""
        logger.info(f"批量加载日K线: {len(symbols)}只股票")
        
        result = {}
        for i, symbol in enumerate(symbols):
            logger.info(f"进度: {i+1}/{len(symbols)} - {symbol}")
            try:
                df = self.load_daily_data(symbol, start_date, end_date, adjust)
                if not df.empty:
                    result[symbol] = df
            except Exception as e:
                logger.warning(f"加载失败: {symbol}, {e}")
        
        logger.info(f"批量加载完成: {len(result)}只股票成功")
        return result