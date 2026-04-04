# -*- coding: utf-8 -*-
"""数据加载器 - AKShare实现"""

from typing import Optional, List, Dict
from pathlib import Path
import pandas as pd
import akshare as ak
from datetime import datetime

from utils.logger import get_logger

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
            # AKShare接口：东方财富日K线
            df = ak.stock_zh_a_hist(
                symbol=symbol,
                period='daily',
                start_date=start_date,
                end_date=end_date,
                adjust=adjust
            )
            
            # 标准化列名
            df = self._standardize_columns(df)
            
            # 添加股票代码
            df['ts_code'] = f"{symbol}.SZ" if symbol.startswith(('0', '3')) else f"{symbol}.SH"
            
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
                # 沪深300成分股
                df = ak.index_stock_cons_weight_csindex(symbol='000300')
                return self._extract_stock_codes(df)
            
            elif pool_name == 'zz500':
                # 中证500成分股
                df = ak.index_stock_cons_weight_csindex(symbol='000905')
                return self._extract_stock_codes(df)
            
            elif pool_name == 'all_a':
                # 全A股列表
                df = ak.stock_info_a_code_name()
                return df['code'].tolist()
            
            else:
                logger.warning(f"未知股票池: {pool_name}")
                return []
                
        except Exception as e:
            logger.error(f"加载股票池失败: {pool_name}, {e}")
            return []
    
    def _extract_stock_codes(self, df: pd.DataFrame) -> List[str]:
        """从指数成分股DataFrame中提取股票代码（兼容多种列名）
        
        修复 BUG-001：AKShare API返回列名可能不同，需兼容处理
        - 成分券代码（新版本）
        - 成分股代码（旧版本）
        - code（其他情况）
        
        Args:
            df: 指数成分股DataFrame
            
        Returns:
            股票代码列表
        """
        # 尝试多种可能的列名
        possible_columns = ['成分券代码', '成分股代码', 'code', '股票代码', 'symbol']
        
        for col in possible_columns:
            if col in df.columns:
                logger.info(f"使用列名 '{col}' 提取股票代码")
                return df[col].tolist()
        
        # 如果都不匹配，记录错误并返回空列表
        logger.error(f"无法找到股票代码列，可用列：{df.columns.tolist()}")
        raise KeyError(f"无法找到股票代码列，可用列：{df.columns.tolist()}")
    
    def load_stock_basic(self) -> pd.DataFrame:
        """加载股票基本信息
        
        Returns:
            股票基本信息DataFrame
        """
        logger.info("加载股票基本信息")
        
        try:
            # A股列表（含上市日期）
            df = ak.stock_info_a_code_name()
            
            # 获取更详细信息
            df_detail = ak.stock_zh_a_spot_em()
            
            # 合并信息
            result = pd.DataFrame()
            result['symbol'] = df['code']
            result['name'] = df['name']
            result['ts_code'] = result['symbol'].apply(
                lambda x: f"{x}.SZ" if x.startswith(('0', '3')) else f"{x}.SH"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"加载股票基本信息失败: {e}")
            return pd.DataFrame()
    
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
            # AKShare交易日历
            df = ak.tool_trade_date_hist_sina()
            
            # 统一日期类型：将 trade_date 转换为字符串格式 (YYYYMMDD)
            df['trade_date'] = df['trade_date'].astype(str).str.replace('-', '')
            
            # 过滤日期范围
            df = df[(df['trade_date'] >= start_date) & (df['trade_date'] <= end_date)]
            
            return df['trade_date'].tolist()
            
        except Exception as e:
            logger.error(f"加载交易日历失败: {e}")
            return []
    
    def load_suspend_info(self, symbol: str) -> pd.DataFrame:
        """加载停牌信息
        
        Args:
            symbol: 股票代码
            
        Returns:
            停牌信息DataFrame
        """
        # AKShare停牌数据接口
        try:
            df = ak.stock_tfp_em()
            if symbol in df['代码'].values:
                return df[df['代码'] == symbol]
            return pd.DataFrame()
        except Exception as e:
            logger.warning(f"停牌信息获取失败: {symbol}, {e}")
            return pd.DataFrame()
    
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
        
        # 日期格式转换
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
        """批量加载日K线数据
        
        Args:
            symbols: 股票代码列表
            start_date: 开始日期
            end_date: 结束日期
            adjust: 复权类型
            
        Returns:
            {symbol: DataFrame} 字典
        """
        logger.info(f"批量加载日K线: {len(symbols)}只股票")
        
        result = {}
        for i, symbol in enumerate(symbols):
            logger.info(f"进度: {i+1}/{len(symbols)} - {symbol}")
            df = self.load_daily_data(symbol, start_date, end_date, adjust)
            if not df.empty:
                result[symbol] = df
        
        logger.info(f"批量加载完成: {len(result)}只股票")
        return result