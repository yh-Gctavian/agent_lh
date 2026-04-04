# -*- coding: utf-8 -*-
"""Data loader module - AKShare implementation"""

from typing import Optional, List, Dict
from pathlib import Path
import pandas as pd
import logging

logger = logging.getLogger('data_loader')


class DataLoader:
    """Data loader based on AKShare"""
    
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
        """Load daily K-line data"""
        logger.info(f"Loading daily data: {symbol}, {start_date}-{end_date}")
        
        try:
            import akshare as ak
            df = ak.stock_zh_a_hist(
                symbol=symbol,
                period='daily',
                start_date=start_date,
                end_date=end_date,
                adjust=adjust
            )
            
            if df is None or df.empty:
                logger.warning(f"No data found: {symbol}")
                return pd.DataFrame()
            
            df = self._standardize_columns(df)
            df['ts_code'] = f"{symbol}.SZ" if symbol.startswith(('0', '3')) else f"{symbol}.SH"
            
            return df
            
        except Exception as e:
            logger.error(f"Failed to load data: {symbol}, {e}")
            return pd.DataFrame()
    
    def load_stock_pool(self, pool_name: str) -> List[str]:
        """Load stock pool"""
        logger.info(f"Loading stock pool: {pool_name}")
        
        try:
            import akshare as ak
            
            if pool_name == 'hs300':
                df = ak.index_stock_cons_weight_csindex(symbol='000300')
                return self._extract_stock_codes(df)
            elif pool_name == 'all_a':
                df = ak.stock_info_a_code_name()
                return df['code'].tolist() if 'code' in df.columns else []
            else:
                return []
                
        except Exception as e:
            logger.error(f"Failed to load stock pool: {pool_name}, {e}")
            return []
    
    def _extract_stock_codes(self, df: pd.DataFrame) -> List[str]:
        """Extract stock codes from DataFrame"""
        for col in ['成分股代码', '代码', 'code', 'symbol']:
            if col in df.columns:
                return df[col].astype(str).str.zfill(6).tolist()
        return []
    
    def _standardize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Standardize column names"""
        column_map = {
            '日期': 'trade_date',
            '开盘': 'open',
            '收盘': 'close',
            '最高': 'high',
            '最低': 'low',
            '成交量': 'volume',
            '成交额': 'amount',
            '换手率': 'turn'
        }
        
        df = df.rename(columns=column_map)
        
        if 'trade_date' in df.columns:
            df['trade_date'] = pd.to_datetime(df['trade_date'])
        
        return df