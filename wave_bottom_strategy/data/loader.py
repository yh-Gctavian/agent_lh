# -*- coding: utf-8 -*-
"""Data loader module - 混合模式（通达信优先，AKShare兜底）"""

from typing import Optional, List, Dict, Literal
from pathlib import Path
import pandas as pd
import logging

from .tdx_loader import TdxLocalLoader, create_tdx_loader
from wave_bottom_strategy.utils.logger import get_logger

logger = get_logger('data_loader')


class DataLoader:
    """数据加载器 - 混合模式
    
    数据源优先级：
    1. 通达信本地数据（vipdoc/*.day） - 离线、快速
    2. AKShare在线数据 - 兜底、完整
    
    优势：
    - 通达信数据本地读取，无需网络，速度快
    - AKShare作为备用，确保数据完整性
    - 自动处理数据格式统一
    """
    
    # 数据源模式
    SOURCE_TDX = 'tdx'      # 仅通达信
    SOURCE_AKSHARE = 'akshare'  # 仅AKShare
    SOURCE_HYBRID = 'hybrid'    # 混合模式（默认）
    
    def __init__(
        self,
        cache_dir: Path = None,
        source_mode: Literal['tdx', 'akshare', 'hybrid'] = 'hybrid',
        tdx_path: str = None,
        adjust: str = 'qfq'
    ):
        """初始化
        
        Args:
            cache_dir: 缓存目录
            source_mode: 数据源模式
            tdx_path: 通达信路径（默认 E:\\new_tdx）
            adjust: 复权方式（qfq前复权/hfq后复权/None不复权）
        """
        self.cache_dir = cache_dir or Path('data/cache')
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self.source_mode = source_mode
        self.adjust = adjust
        
        # 初始化通达信加载器
        if source_mode in ['tdx', 'hybrid']:
            self.tdx_loader = create_tdx_loader(local=True, tdx_path=tdx_path)
            logger.info(f"通达信数据源已启用")
        
        # 统计信息
        self.stats = {
            'tdx_success': 0,
            'tdx_fail': 0,
            'akshare_success': 0,
            'akshare_fail': 0
        }
    
    def load_daily_data(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
        adjust: str = None
    ) -> pd.DataFrame:
        """加载日K线数据
        
        Args:
            symbol: 股票代码（6位数字）
            start_date: 开始日期
            end_date: 结束日期
            adjust: 复权方式（覆盖默认设置）
            
        Returns:
            日K线DataFrame
        """
        adjust = adjust or self.adjust
        logger.info(f"加载日K线: {symbol}, {start_date}-{end_date}, 模式={self.source_mode}")
        
        df = pd.DataFrame()
        
        # 优先尝试通达信
        if self.source_mode in ['tdx', 'hybrid']:
            df = self._load_from_tdx(symbol, start_date, end_date)
            
            if not df.empty:
                self.stats['tdx_success'] += 1
                
                # 通达信数据通常未复权，需要复权处理
                if adjust and adjust != 'none':
                    df = self._apply_adjust(df, symbol, adjust)
                
                return df
            else:
                self.stats['tdx_fail'] += 1
                logger.info(f"通达信无数据，尝试AKShare: {symbol}")
        
        # AKShare兜底
        if self.source_mode in ['akshare', 'hybrid']:
            df = self._load_from_akshare(symbol, start_date, end_date, adjust)
            
            if not df.empty:
                self.stats['akshare_success'] += 1
            else:
                self.stats['akshare_fail'] += 1
        
        return df
    
    def _load_from_tdx(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        """从通达信加载数据
        
        Args:
            symbol: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            DataFrame
        """
        try:
            df = self.tdx_loader.load_daily_data(symbol, start_date, end_date)
            
            if df.empty:
                return df
            
            # 标准化日期格式
            df['trade_date'] = pd.to_datetime(df['trade_date'])
            
            # 确保数值类型
            for col in ['open', 'high', 'low', 'close', 'volume', 'amount']:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
            
            return df
            
        except Exception as e:
            logger.warning(f"通达信加载失败: {symbol}, {e}")
            return pd.DataFrame()
    
    def _load_from_akshare(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
        adjust: str
    ) -> pd.DataFrame:
        """从AKShare加载数据
        
        Args:
            symbol: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            adjust: 复权方式
            
        Returns:
            DataFrame
        """
        try:
            import akshare as ak
            
            # 标准化日期格式（AKShare需要 YYYYMMDD）
            start_str = start_date.replace('-', '')
            end_str = end_date.replace('-', '')
            
            df = ak.stock_zh_a_hist(
                symbol=symbol,
                period='daily',
                start_date=start_str,
                end_date=end_str,
                adjust=adjust
            )
            
            if df is None or df.empty:
                logger.warning(f"AKShare无数据: {symbol}")
                return pd.DataFrame()
            
            df = self._standardize_columns(df)
            
            # 添加 ts_code
            if symbol.startswith('6'):
                df['ts_code'] = f"{symbol}.SH"
            elif symbol.startswith(('0', '3')):
                df['ts_code'] = f"{symbol}.SZ"
            else:
                df['ts_code'] = f"{symbol}.BJ"
            
            return df
            
        except Exception as e:
            logger.error(f"AKShare加载失败: {symbol}, {e}")
            return pd.DataFrame()
    
    def _apply_adjust(self, df: pd.DataFrame, symbol: str, adjust: str) -> pd.DataFrame:
        """应用复权处理
        
        通达信本地数据通常是原始价格（未复权）
        需要从AKShare获取复权因子进行复权
        
        Args:
            df: 未复权数据
            symbol: 股票代码
            adjust: 复权方式
            
        Returns:
            复权后的数据
        """
        # 简化处理：暂时返回原始数据
        # 复权处理可由 processor.py 统一处理
        logger.info(f"复权处理由 processor 模块处理: {symbol}")
        return df
    
    def load_stock_pool(self, pool_name: str) -> List[str]:
        """加载股票池
        
        Args:
            pool_name: 股票池名称
                - 'hs300': 沪深300成分股
                - 'all_a': 全A股
                - 'all_sh': 上海全市场
                - 'all_sz': 深圳全市场
            
        Returns:
            股票代码列表
        """
        logger.info(f"加载股票池: {pool_name}")
        
        # 通达信可直接获取本地股票列表
        if pool_name in ['all_sh', 'all_sz', 'all_a']:
            return self.tdx_loader.load_stock_pool(pool_name)
        
        # 指数成分股需从AKShare获取
        try:
            import akshare as ak
            
            if pool_name == 'hs300':
                df = ak.index_stock_cons_weight_csindex(symbol='000300')
                return self._extract_stock_codes(df)
            elif pool_name == 'zz500':
                df = ak.index_stock_cons_weight_csindex(symbol='000905')
                return self._extract_stock_codes(df)
            else:
                logger.warning(f"不支持的股票池: {pool_name}")
                return []
                
        except Exception as e:
            logger.error(f"加载股票池失败: {pool_name}, {e}")
            return []
    
    def _extract_stock_codes(self, df: pd.DataFrame) -> List[str]:
        """从DataFrame提取股票代码
        
        注意：AKShare不同接口返回的列名可能不同：
        - index_stock_cons_weight_csindex: '成分券代码'
        - index_stock_cons: '成分股代码'
        """
        # 支持多种列名格式
        possible_cols = [
            '成分券代码',   # AKShare index_stock_cons_weight_csindex 返回
            '成分股代码',   # AKShare index_stock_cons 返回
            '代码',
            'code',
            'symbol',
            '股票代码'
        ]
        
        for col in possible_cols:
            if col in df.columns:
                codes = df[col].astype(str).str.zfill(6).tolist()
                logger.info(f"从列 '{col}' 提取到 {len(codes)} 个股票代码")
                return codes
        
        logger.warning(f"未找到股票代码列，可用列: {df.columns.tolist()}")
        return []
    
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
            '换手率': 'turn',
            '振幅': 'amplitude',
            '涨跌幅': 'pct_change',
            '涨跌额': 'change'
        }
        
        df = df.rename(columns=column_map)
        
        if 'trade_date' in df.columns:
            df['trade_date'] = pd.to_datetime(df['trade_date'])
        
        return df
    
    def get_stats(self) -> Dict:
        """获取加载统计"""
        return self.stats.copy()
    
    def check_tdx_availability(self, symbol: str) -> Dict:
        """检查通达信数据可用性
        
        Args:
            symbol: 股票代码
            
        Returns:
            数据可用性信息
        """
        if hasattr(self.tdx_loader, 'get_data_coverage'):
            return self.tdx_loader.get_data_coverage(symbol)
        return {'has_data': False}
    
    def load_multiple(
        self,
        symbols: List[str],
        start_date: str,
        end_date: str,
        adjust: str = None
    ) -> Dict[str, pd.DataFrame]:
        """批量加载多只股票数据
        
        Args:
            symbols: 股票代码列表
            start_date: 开始日期
            end_date: 结束日期
            adjust: 复权方式
            
        Returns:
            {symbol: DataFrame} 字典
        """
        results = {}
        
        for symbol in symbols:
            df = self.load_daily_data(symbol, start_date, end_date, adjust)
            if not df.empty:
                results[symbol] = df
        
        logger.info(f"批量加载完成: {len(results)}/{len(symbols)}只股票有数据")
        return results


# 便捷函数
def load_data(
    symbol: str,
    start_date: str,
    end_date: str,
    source: str = 'hybrid'
) -> pd.DataFrame:
    """便捷加载函数
    
    Args:
        symbol: 股票代码
        start_date: 开始日期
        end_date: 结束日期
        source: 数据源
        
    Returns:
        日K线数据
    """
    loader = DataLoader(source_mode=source)
    return loader.load_daily_data(symbol, start_date, end_date)