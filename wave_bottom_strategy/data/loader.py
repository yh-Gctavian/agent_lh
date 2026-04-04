# -*- coding: utf-8 -*-
"""数据加载器 - AKShare实现"""

from typing import Optional, List, Dict
from pathlib import Path
import pandas as pd
import akshare as ak
from datetime import datetime
import time

from ..utils.logger import get_logger

logger = get_logger('data_loader')


class DataLoader:
    """数据加载器 - 基于AKShare"""
    
    def __init__(self, cache_dir: Path = None):
        self.cache_dir = cache_dir or Path('data/cache')
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def load_daily_data(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
        adjust: str = 'qfq'
    ) -> pd.DataFrame:
        """加载日K线数据
        
        Args:
            symbol: 股票代码 (如 000001)
            start_date: 开始日期 (YYYYMMDD)
            end_date: 结束日期 (YYYYMMDD)
            adjust: 复权类型 ('qfq'前复权, 'hfq'后复权, ''不复权)
            
        Returns:
            日K线DataFrame
        """
        logger.info(f"加载日K线: {symbol}, {start_date}-{end_date}")
        
        try:
            df = ak.stock_zh_a_hist(
                symbol=symbol,
                period='daily',
                start_date=start_date,
                end_date=end_date,
                adjust=adjust
            )
            
            df = self._standardize_columns(df)
            
            if symbol.startswith(('0', '3')):
                df['ts_code'] = f"{symbol}.SZ"
            else:
                df['ts_code'] = f"{symbol}.SH"
            
            return df
            
        except Exception as e:
            logger.error(f"加载日K线失败: {symbol}, {e}")
            return pd.DataFrame()
    
    def load_stock_pool(self, pool_name: str) -> List[str]:
        """加载股票池
        
        Args:
            pool_name: 股票池名称 (hs300, zz500, all_a)
            
        Returns:
            股票代码列表
        """
        logger.info(f"加载股票池: {pool_name}")
        
        try:
            if pool_name == 'hs300':
                df = ak.index_stock_cons_weight_csindex(symbol='000300')
                codes = df['成分股代码'].tolist() if '成分股代码' in df.columns else df.iloc[:, 0].tolist()
                return codes
            
            elif pool_name == 'zz500':
                df = ak.index_stock_cons_weight_csindex(symbol='000905')
                codes = df['成分股代码'].tolist() if '成分股代码' in df.columns else df.iloc[:, 0].tolist()
                return codes
            
            elif pool_name == 'all_a':
                df = ak.stock_info_a_code_name()
                return df['code'].tolist()
            
            else:
                logger.warning(f"未知股票池: {pool_name}")
                return []
                
        except Exception as e:
            logger.error(f"加载股票池失败: {pool_name}, {e}")
            return []
    
    def load_trade_calendar(self, start_date: str, end_date: str) -> List[str]:
        """加载交易日历
        
        Args:
            start_date: 开始日期 (YYYYMMDD)
            end_date: 结束日期 (YYYYMMDD)
            
        Returns:
            交易日列表
        """
        logger.info(f"加载交易日历: {start_date}-{end_date}")
        
        try:
            df = ak.tool_trade_date_hist_sina()
            df = df[(df['trade_date'] >= start_date) & (df['trade_date'] <= end_date)]
            return df['trade_date'].tolist()
        except Exception as e:
            logger.error(f"加载交易日历失败: {e}")
            return []
    
    def _standardize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """标准化列名
        
        Args:
            df: 原始DataFrame
            
        Returns:
            标准化后的DataFrame
        """
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