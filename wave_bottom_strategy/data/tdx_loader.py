# -*- coding: utf-8 -*-
"""TDX Data Loader - Read data from TongDaXin locally"""

from typing import List, Optional
from pathlib import Path
import pandas as pd
import logging

logger = logging.getLogger('tdx_loader')


class TdxDataLoader:
    """TongDaXin data loader - Read local TDX data without network"""
    
    def __init__(self, tdx_path: str = None):
        """Initialize TDX loader
        
        Args:
            tdx_path: TDX installation path, e.g. 'C:/new_tdx'
        """
        self.tdx_path = Path(tdx_path) if tdx_path else Path('C:/new_tdx')
        self._api = None
    
    def _get_api(self):
        """Get or create TDX API connection"""
        if self._api is None:
            try:
                from pytdx.hq import TdxHq_API
                self._api = TdxHq_API()
            except ImportError:
                logger.warning("pytdx not installed. Run: pip install pytdx")
                return None
        return self._api
    
    def load_daily_data(
        self,
        symbol: str,
        start_date: str = None,
        end_date: str = None
    ) -> pd.DataFrame:
        """Load daily K-line data from TDX
        
        Args:
            symbol: Stock code, e.g. '000001'
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            
        Returns:
            DataFrame with OHLCV data
        """
        api = self._get_api()
        if api is None:
            return pd.DataFrame()
        
        # Determine market: 0=SZ, 1=SH
        market = 0 if symbol.startswith(('0', '3')) else 1
        
        try:
            # Connect to TDX server (use any available server)
            # Or use local file reading
            data = self._read_local_tdx(symbol, market)
            
            if data.empty:
                logger.warning("No data found for %s" % symbol)
                return pd.DataFrame()
            
            # Filter by date range
            if start_date:
                data = data[data['trade_date'] >= start_date]
            if end_date:
                data = data[data['trade_date'] <= end_date]
            
            return data
            
        except Exception as e:
            logger.error("Failed to load data for %s: %s" % (symbol, e))
            return pd.DataFrame()
    
    def _read_local_tdx(self, symbol: str, market: int) -> pd.DataFrame:
        """Read TDX local .day file
        
        Args:
            symbol: Stock code
            market: 0=SZ, 1=SH
            
        Returns:
            DataFrame with OHLCV data
        """
        import struct
        
        # TDX day file path
        market_dir = 'sz' if market == 0 else 'sh'
        day_file = self.tdx_path / 'vipdoc' / market_dir / 'lday' / ('%s.day' % symbol)
        
        if not day_file.exists():
            logger.warning("TDX day file not found: %s" % day_file)
            return pd.DataFrame()
        
        data = []
        with open(day_file, 'rb') as f:
            while True:
                chunk = f.read(32)
                if not chunk or len(chunk) < 32:
                    break
                
                # Parse 32-byte record
                # Format: date(4), open(4), high(4), low(4), close(4), amount(4), volume(4)
                values = struct.unpack('IIIIIII', chunk)
                
                date_int = values[0]
                year = date_int // 10000
                month = (date_int % 10000) // 100
                day = date_int % 100
                
                data.append({
                    'trade_date': '%04d-%02d-%02d' % (year, month, day),
                    'open': values[1] / 100.0,
                    'high': values[2] / 100.0,
                    'low': values[3] / 100.0,
                    'close': values[4] / 100.0,
                    'amount': values[5],
                    'volume': values[6]
                })
        
        df = pd.DataFrame(data)
        df['trade_date'] = pd.to_datetime(df['trade_date'])
        df['ts_code'] = '%s.%s' % (symbol, 'SZ' if market == 0 else 'SH')
        
        logger.info("Loaded %d records from TDX for %s" % (len(df), symbol))
        return df
    
    def load_stock_pool(self, pool_name: str) -> List[str]:
        """Load stock pool from TDX
        
        Args:
            pool_name: Pool name (hs300, zz500, all_a)
            
        Returns:
            List of stock codes
        """
        # Read from TDX block files
        block_file = self.tdx_path / 'T0002' / 'hq_cache' / ('%s.txt' % pool_name)
        
        if block_file.exists():
            with open(block_file, 'r', encoding='gbk') as f:
                codes = [line.strip() for line in f if line.strip()]
            return codes
        
        logger.warning("Block file not found: %s" % block_file)
        return []
    
    def get_realtime_quotes(self, symbols: List[str]) -> pd.DataFrame:
        """Get realtime quotes (requires network)
        
        Args:
            symbols: List of stock codes
            
        Returns:
            DataFrame with realtime data
        """
        api = self._get_api()
        if api is None:
            return pd.DataFrame()
        
        try:
            # Connect to TDX server
            # Use standard TDX server
            if not api.connect('119.147.212.81', 7709):
                logger.error("Failed to connect to TDX server")
                return pd.DataFrame()
            
            data = []
            for symbol in symbols:
                market = 0 if symbol.startswith(('0', '3')) else 1
                quotes = api.get_security_quotes([(market, symbol)])
                if quotes:
                    data.extend(quotes)
            
            api.disconnect()
            return pd.DataFrame(data)
            
        except Exception as e:
            logger.error("Failed to get realtime quotes: %s" % e)
            return pd.DataFrame()


# Fallback to AKShare if TDX not available
class HybridDataLoader:
    """Hybrid loader - Try TDX first, fallback to AKShare"""
    
    def __init__(self, tdx_path: str = None):
        self.tdx_loader = TdxDataLoader(tdx_path)
        self._akshare_loader = None
    
    def _get_akshare_loader(self):
        """Get AKShare loader as fallback"""
        if self._akshare_loader is None:
            from data.loader import DataLoader
            self._akshare_loader = DataLoader()
        return self._akshare_loader
    
    def load_daily_data(self, symbol: str, start_date: str = None, end_date: str = None) -> pd.DataFrame:
        """Load data - Try TDX first, then AKShare"""
        # Try TDX first
        data = self.tdx_loader.load_daily_data(symbol, start_date, end_date)
        
        if not data.empty:
            return data
        
        # Fallback to AKShare
        logger.info("TDX data not available, using AKShare for %s" % symbol)
        akshare = self._get_akshare_loader()
        
        start = start_date.replace('-', '') if start_date else '20200101'
        end = end_date.replace('-', '') if end_date else '20251231'
        
        return akshare.load_daily_data(symbol, start, end)