# -*- coding: utf-8 -*-
"""数据加载器 - AKShare实现

特性：
- 支持3次网络重试
- 支持本地缓存fallback
- 失败时抛出明确异常
"""

from typing import Optional, List, Dict
from pathlib import Path
import pandas as pd
import akshare as ak
from datetime import datetime
import time
import json

from utils.logger import get_logger

logger = get_logger('data_loader')


# ============================================================================
# 自定义异常
# ============================================================================

class DataLoaderError(Exception):
    """数据加载器异常基类"""
    pass


class NetworkError(DataLoaderError):
    """网络请求异常"""
    pass


class DataNotFoundError(DataLoaderError):
    """数据未找到异常"""
    pass


# ============================================================================
# 数据加载器
# ============================================================================

class DataLoader:
    """数据加载器 - 基于AKShare
    
    特性：
    - 支持3次网络重试
    - 支持本地缓存fallback
    - 失败时抛出明确异常
    """
    
    MAX_RETRIES = 3
    RETRY_DELAY = 1.0  # 秒
    
    def __init__(self, cache_dir: Path = None):
        self.cache_dir = cache_dir or Path('data/cache')
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def _retry_request(self, func, *args, **kwargs):
        """网络请求重试包装器
        
        Args:
            func: 要执行的函数
            *args, **kwargs: 函数参数
            
        Returns:
            函数返回值
            
        Raises:
            NetworkError: 重试次数耗尽后仍失败
        """
        last_error = None
        
        for attempt in range(self.MAX_RETRIES):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_error = e
                error_msg = str(e)
                
                # 检查是否为网络相关错误
                is_network_error = any(keyword in error_msg.lower() for keyword in [
                    'connection', 'timeout', 'network', 'proxy', 'http', 'ssl'
                ])
                
                if is_network_error and attempt < self.MAX_RETRIES - 1:
                    logger.warning(f"网络请求失败(尝试 {attempt + 1}/{self.MAX_RETRIES}): {e}")
                    time.sleep(self.RETRY_DELAY * (attempt + 1))  # 递增延迟
                else:
                    raise
        
        # 所有重试都失败
        raise NetworkError(f"网络请求失败，已重试{self.MAX_RETRIES}次: {last_error}")
    
    def _get_cache_path(self, cache_key: str) -> Path:
        """获取缓存文件路径"""
        return self.cache_dir / f"{cache_key}.json"
    
    def _load_cache(self, cache_key: str) -> Optional[pd.DataFrame]:
        """加载本地缓存
        
        Args:
            cache_key: 缓存键名
            
        Returns:
            缓存的DataFrame，不存在返回None
        """
        cache_path = self._get_cache_path(cache_key)
        if cache_path.exists():
            try:
                with open(cache_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                df = pd.DataFrame(data['records'])
                logger.info(f"从缓存加载数据: {cache_key}")
                return df
            except Exception as e:
                logger.warning(f"缓存加载失败: {cache_key}, {e}")
        return None
    
    def _save_cache(self, cache_key: str, df: pd.DataFrame):
        """保存到本地缓存
        
        Args:
            cache_key: 缓存键名
            df: 要缓存的DataFrame
        """
        cache_path = self._get_cache_path(cache_key)
        try:
            data = {
                'records': df.to_dict('records'),
                'cached_at': datetime.now().isoformat()
            }
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.info(f"数据已缓存: {cache_key}")
        except Exception as e:
            logger.warning(f"缓存保存失败: {cache_key}, {e}")
    
    # ========================================================================
    # 日K线数据
    # ========================================================================
    
    def load_daily_data(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
        adjust: str = 'qfq',
        use_cache: bool = True
    ) -> pd.DataFrame:
        """加载日K线数据
        
        Args:
            symbol: 股票代码 (如 000001)
            start_date: 开始日期 (YYYYMMDD)
            end_date: 结束日期 (YYYYMMDD)
            adjust: 复权类型 ('qfq'前复权, 'hfq'后复权, ''不复权)
            use_cache: 是否使用缓存fallback
            
        Returns:
            日K线DataFrame
            
        Raises:
            NetworkError: 网络请求失败且无缓存
            DataNotFoundError: 数据不存在
        """
        logger.info(f"加载日K线: {symbol}, {start_date}-{end_date}")
        
        cache_key = f"daily_{symbol}_{start_date}_{end_date}_{adjust}"
        
        try:
            # 尝试网络请求（带重试）
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
            
            # 标准化列名
            df = self._standardize_columns(df)
            
            # 添加股票代码
            df['ts_code'] = f"{symbol}.SZ" if symbol.startswith(('0', '3')) else f"{symbol}.SH"
            
            # 保存缓存
            if use_cache:
                self._save_cache(cache_key, df)
            
            return df
            
        except NetworkError as e:
            # 网络失败，尝试加载缓存
            if use_cache:
                logger.warning(f"网络请求失败，尝试加载缓存: {symbol}")
                cached_df = self._load_cache(cache_key)
                if cached_df is not None:
                    return cached_df
            
            # 无缓存，抛出异常
            logger.error(f"加载日K线失败: {symbol}, {e}")
            raise NetworkError(f"无法加载日K线数据，网络失败且无缓存: {symbol}") from e
            
        except DataNotFoundError:
            raise
            
        except Exception as e:
            logger.error(f"加载日K线失败: {symbol}, {e}")
            raise DataLoaderError(f"加载日K线失败: {symbol}, {e}") from e
    
    # ========================================================================
    # 股票池
    # ========================================================================
    
    def load_stock_pool(self, pool_name: str, use_cache: bool = True) -> List[str]:
        """加载股票池
        
        Args:
            pool_name: 股票池名称 (hs300, zz500, all_a)
            use_cache: 是否使用缓存fallback
            
        Returns:
            股票代码列表
            
        Raises:
            NetworkError: 网络请求失败且无缓存
            ValueError: 未知的股票池名称
        """
        logger.info(f"加载股票池: {pool_name}")
        
        cache_key = f"pool_{pool_name}"
        
        # 验证股票池名称
        valid_pools = ['hs300', 'zz500', 'all_a']
        if pool_name not in valid_pools:
            raise ValueError(f"未知股票池: {pool_name}，有效值: {valid_pools}")
        
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
            
            # 保存缓存
            if use_cache and codes:
                cache_path = self._get_cache_path(cache_key)
                try:
                    with open(cache_path, 'w', encoding='utf-8') as f:
                        json.dump({'codes': codes, 'cached_at': datetime.now().isoformat()}, f)
                except Exception:
                    pass
            
            logger.info(f"股票池加载成功: {pool_name}, {len(codes)}只股票")
            return codes
                
        except NetworkError as e:
            # 网络失败，尝试加载缓存
            if use_cache:
                logger.warning(f"网络请求失败，尝试加载缓存: {pool_name}")
                cache_path = self._get_cache_path(cache_key)
                if cache_path.exists():
                    try:
                        with open(cache_path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                        return data.get('codes', [])
                    except Exception:
                        pass
            
            logger.error(f"加载股票池失败: {pool_name}, {e}")
            raise NetworkError(f"无法加载股票池，网络失败且无缓存: {pool_name}") from e
            
        except Exception as e:
            logger.error(f"加载股票池失败: {pool_name}, {e}")
            raise DataLoaderError(f"加载股票池失败: {pool_name}, {e}") from e
    
    def _extract_stock_codes(self, df: pd.DataFrame) -> List[str]:
        """从指数成分股DataFrame中提取股票代码（兼容多种列名）
        
        修复：AKShare API返回列名可能不同，需兼容处理
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
        
        # 如果都不匹配，记录错误并抛出异常
        available_cols = df.columns.tolist()
        logger.error(f"无法找到股票代码列，可用列：{available_cols}")
        raise KeyError(f"无法找到股票代码列，可用列：{available_cols}")
    
    # ========================================================================
    # 股票基本信息
    # ========================================================================
    
    def load_stock_basic(self) -> pd.DataFrame:
        """加载股票基本信息
        
        Returns:
            股票基本信息DataFrame
            
        Raises:
            NetworkError: 网络请求失败
        """
        logger.info("加载股票基本信息")
        
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
            raise NetworkError(f"加载股票基本信息失败: {e}") from e
    
    # ========================================================================
    # 交易日历
    # ========================================================================
    
    def load_trade_calendar(self, start_date: str, end_date: str) -> List[str]:
        """加载交易日历
        
        Args:
            start_date: 开始日期 (YYYYMMDD)
            end_date: 结束日期 (YYYYMMDD)
            
        Returns:
            交易日列表
            
        Raises:
            NetworkError: 网络请求失败
        """
        logger.info(f"加载交易日历: {start_date}-{end_date}")
        
        try:
            df = self._retry_request(ak.tool_trade_date_hist_sina)
            
            # 修复：健壮的日期类型转换
            # AKShare可能返回整数(int)、字符串(str)或datetime类型
            # 统一转换为YYYYMMDD格式的字符串
            df['trade_date'] = pd.to_datetime(df['trade_date'], format='mixed').dt.strftime('%Y%m%d')
            
            # 过滤日期范围
            df = df[(df['trade_date'] >= start_date) & (df['trade_date'] <= end_date)]
            
            return df['trade_date'].tolist()
            
        except Exception as e:
            logger.error(f"加载交易日历失败: {e}")
            raise NetworkError(f"加载交易日历失败: {e}") from e
    
    # ========================================================================
    # 停牌信息
    # ========================================================================
    
    def load_suspend_info(self, symbol: str = None) -> pd.DataFrame:
        """加载停牌信息
        
        Args:
            symbol: 股票代码（可选，不传则返回全部）
            
        Returns:
            停牌信息DataFrame
        """
        try:
            df = self._retry_request(ak.stock_tfp_em)
            if symbol and '代码' in df.columns:
                return df[df['代码'] == symbol]
            return df
        except Exception as e:
            logger.warning(f"停牌信息获取失败: {symbol}, {e}")
            return pd.DataFrame()
    
    # ========================================================================
    # 工具方法
    # ========================================================================
    
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
        adjust: str = 'qfq',
        continue_on_error: bool = True
    ) -> Dict[str, pd.DataFrame]:
        """批量加载日K线数据
        
        Args:
            symbols: 股票代码列表
            start_date: 开始日期
            end_date: 结束日期
            adjust: 复权类型
            continue_on_error: 失败时是否继续
            
        Returns:
            {symbol: DataFrame} 字典
        """
        logger.info(f"批量加载日K线: {len(symbols)}只股票")
        
        result = {}
        errors = []
        
        for i, symbol in enumerate(symbols):
            logger.info(f"进度: {i+1}/{len(symbols)} - {symbol}")
            try:
                df = self.load_daily_data(symbol, start_date, end_date, adjust)
                if not df.empty:
                    result[symbol] = df
            except Exception as e:
                error_msg = f"{symbol}: {e}"
                errors.append(error_msg)
                logger.warning(f"加载失败: {error_msg}")
                
                if not continue_on_error:
                    raise
        
        logger.info(f"批量加载完成: {len(result)}只股票成功, {len(errors)}只失败")
        
        if errors:
            logger.warning(f"失败股票: {errors}")
        
        return result