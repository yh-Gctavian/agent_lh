# -*- coding: utf-8 -*-
"""通达信本地数据读取器 - pytdx实现"""

from typing import Optional, List, Dict
from pathlib import Path
from datetime import datetime
import pandas as pd
import numpy as np
import struct
import os

from wave_bottom_strategy.utils.logger import get_logger

logger = get_logger('tdx_loader')


class TdxLocalLoader:
    """通达信本地数据读取器
    
    读取 vipdoc 目录下的 .day 文件（日K线数据）
    数据格式：每条记录32字节
    - 日期(4字节) + 开盘(4字节) + 最高(4字节) + 最低(4字节) + 收盘(4字节) + 成交额(4字节) + 成交量(4字节) + 保留(4字节)
    """
    
    # 通达信数据路径
    TDX_ROOT: Path = Path(r"E:\new_tdx")
    VIPDOC_DIR: Path = TDX_ROOT / "vipdoc"
    
    # 市场代码映射
    MARKET_MAP = {
        'sh': {'code': 1, 'suffix': '.SH', 'lday': 'sh/lday'},  # 上海
        'sz': {'code': 0, 'suffix': '.SZ', 'lday': 'sz/lday'},  # 深圳
        'bj': {'code': 0, 'suffix': '.BJ', 'lday': 'bj/lday'},  # 北交所
    }
    
    # 通达信每条记录32字节
    DAY_RECORD_SIZE = 32
    
    def __init__(self, tdx_path: str = None):
        """初始化
        
        Args:
            tdx_path: 通达信根目录，默认 E:\\new_tdx
        """
        if tdx_path:
            self.TDX_ROOT = Path(tdx_path)
            self.VIPDOC_DIR = self.TDX_ROOT / "vipdoc"
        
        # 验证路径
        if not self.VIPDOC_DIR.exists():
            logger.warning(f"通达信路径不存在: {self.VIPDOC_DIR}")
        
        logger.info(f"通达信数据路径: {self.VIPDOC_DIR}")
    
    def load_daily_data(
        self,
        symbol: str,
        start_date: str = None,
        end_date: str = None
    ) -> pd.DataFrame:
        """加载日K线数据
        
        Args:
            symbol: 股票代码（6位数字，如 '000001'）
            start_date: 开始日期（格式：YYYYMMDD 或 YYYY-MM-DD）
            end_date: 结束日期
            
        Returns:
            日K线DataFrame
        """
        # 确定市场
        market, ts_code = self._detect_market(symbol)
        
        # 构建文件路径
        file_path = self._get_day_file_path(market, symbol)
        
        if not file_path.exists():
            logger.warning(f"通达信数据文件不存在: {file_path}")
            return pd.DataFrame()
        
        # 读取数据
        df = self._read_day_file(file_path)
        
        if df.empty:
            return df
        
        # 添加 ts_code
        df['ts_code'] = ts_code
        
        # 日期过滤
        if start_date:
            start_date = self._normalize_date(start_date)
            df = df[df['trade_date'] >= start_date]
        
        if end_date:
            end_date = self._normalize_date(end_date)
            df = df[df['trade_date'] <= end_date]
        
        logger.info(f"加载通达信数据: {symbol}, {len(df)}条")
        
        return df
    
    def load_stock_pool(self, pool_name: str) -> List[str]:
        """加载股票池
        
        Args:
            pool_name: 股票池名称
            
        Returns:
            股票代码列表
        """
        if pool_name == 'all_sh':
            return self._list_stocks('sh')
        elif pool_name == 'all_sz':
            return self._list_stocks('sz')
        elif pool_name == 'all_a':
            sh = self._list_stocks('sh')
            sz = self._list_stocks('sz')
            return sh + sz
        else:
            logger.warning(f"不支持的股票池: {pool_name}")
            return []
    
    def _detect_market(self, symbol: str) -> tuple:
        """判断股票市场
        
        Args:
            symbol: 6位股票代码
            
        Returns:
            (市场代码, ts_code)
        """
        # 上海市场：6开头（主板）、60开头（主板）、68开头（科创板）
        if symbol.startswith('6'):
            return 'sh', f"{symbol}.SH"
        
        # 深圳市场：00开头（主板）、30开头（创业板）
        elif symbol.startswith(('0', '3')):
            return 'sz', f"{symbol}.SZ"
        
        # 北交所：8开头、4开头
        elif symbol.startswith(('8', '4')):
            return 'bj', f"{symbol}.BJ"
        
        # 默认深圳
        else:
            return 'sz', f"{symbol}.SZ"
    
    def _get_day_file_path(self, market: str, symbol: str) -> Path:
        """获取日K线文件路径
        
        Args:
            market: 市场代码（sh/sz/bj）
            symbol: 股票代码
            
        Returns:
            文件路径
        """
        market_info = self.MARKET_MAP.get(market, self.MARKET_MAP['sz'])
        lday_dir = self.VIPDOC_DIR / market_info['lday']
        
        # 文件名格式：sh600000.day 或 sz000001.day
        file_name = f"{market}{symbol}.day"
        
        return lday_dir / file_name
    
    def _read_day_file(self, file_path: Path) -> pd.DataFrame:
        """读取 .day 文件
        
        通达信日线文件格式（每条记录32字节）：
        - 日期：4字节整数（YYYYMMDD）
        - 开盘：4字节整数（实际价格 * 100）
        - 最高：4字节整数
        - 最低：4字节整数
        - 收盘：4字节整数
        - 成交额：4字节浮点数
        - 成交量：4字节整数
        - 保留：4字节
        
        Args:
            file_path: .day 文件路径
            
        Returns:
            DataFrame
        """
        try:
            with open(file_path, 'rb') as f:
                data = f.read()
            
            if len(data) == 0:
                return pd.DataFrame()
            
            # 每条记录32字节
            record_count = len(data) // self.DAY_RECORD_SIZE
            
            # 解析数据
            records = []
            for i in range(record_count):
                offset = i * self.DAY_RECORD_SIZE
                record_data = data[offset:offset + self.DAY_RECORD_SIZE]
                
                # 解析字段
                # struct格式：I(日期) IIII(开高低收) I(成交额) I(成交量) I(保留)
                # 通达信实际格式32字节，成交额是整数而非浮点数
                unpacked = struct.unpack('IIIIIIII', record_data)
                
                date_int = unpacked[0]
                open_price = unpacked[1] / 100.0  # 价格需要除以100
                high_price = unpacked[2] / 100.0
                low_price = unpacked[3] / 100.0
                close_price = unpacked[4] / 100.0
                amount = unpacked[5]  # 成交额（元）
                volume = unpacked[6]  # 成交量（手）
                
                # 转换日期
                trade_date = str(date_int)
                
                records.append({
                    'trade_date': trade_date,
                    'open': open_price,
                    'high': high_price,
                    'low': low_price,
                    'close': close_price,
                    'volume': volume,
                    'amount': amount
                })
            
            df = pd.DataFrame(records)
            
            # 添加常用字段
            df['turn'] = 0  # 通达信本地数据无换手率
            df['is_suspended'] = False
            
            return df
            
        except Exception as e:
            logger.error(f"读取 .day 文件失败: {file_path}, {e}")
            return pd.DataFrame()
    
    def _list_stocks(self, market: str) -> List[str]:
        """列出市场所有股票
        
        Args:
            market: 市场代码
            
        Returns:
            股票代码列表
        """
        market_info = self.MARKET_MAP.get(market, self.MARKET_MAP['sz'])
        lday_dir = self.VIPDOC_DIR / market_info['lday']
        
        if not lday_dir.exists():
            logger.warning(f"目录不存在: {lday_dir}")
            return []
        
        stocks = []
        for file in lday_dir.glob(f"{market}*.day"):
            # 文件名如 sh600000.day，提取 600000
            code = file.stem[2:]  # 去掉市场前缀
            if len(code) == 6 and code.isdigit():
                stocks.append(code)
        
        logger.info(f"{market}市场股票数: {len(stocks)}")
        return stocks
    
    def _normalize_date(self, date_str: str) -> str:
        """标准化日期格式
        
        Args:
            date_str: 日期字符串
            
        Returns:
            YYYYMMDD 格式
        """
        if '-' in date_str:
            return date_str.replace('-', '')
        return date_str
    
    def get_data_coverage(self, symbol: str) -> Dict:
        """获取数据覆盖范围
        
        Args:
            symbol: 股票代码
            
        Returns:
            数据范围信息
        """
        df = self.load_daily_data(symbol)
        
        if df.empty:
            return {'has_data': False}
        
        return {
            'has_data': True,
            'start_date': df['trade_date'].min(),
            'end_date': df['trade_date'].max(),
            'record_count': len(df)
        }
    
    def check_data_availability(self, symbol: str, date: str) -> bool:
        """检查指定日期是否有数据
        
        Args:
            symbol: 股票代码
            date: 日期
            
        Returns:
            是否有数据
        """
        df = self.load_daily_data(symbol, date, date)
        return not df.empty


class TdxOnlineLoader:
    """通达信在线数据读取器（通过 pytdx 标准接口）
    
    使用 pytdx 的标准接口连接通达信服务器获取数据
    可作为本地数据的补充
    """
    
    def __init__(self, host: str = '119.147.212.81', port: int = 7709):
        """初始化
        
        Args:
            host: 通达信服务器地址
            port: 端口
        """
        self.host = host
        self.port = port
        self.api = None
    
    def connect(self):
        """连接服务器"""
        try:
            from pytdx.hq import TdxHq_API
            
            self.api = TdxHq_API()
            self.api.connect(self.host, self.port)
            logger.info(f"连接通达信服务器: {self.host}:{self.port}")
            return True
        except Exception as e:
            logger.error(f"连接失败: {e}")
            return False
    
    def disconnect(self):
        """断开连接"""
        if self.api:
            self.api.disconnect()
    
    def get_security_list(self, market: int, start: int = 0) -> List:
        """获取股票列表
        
        Args:
            market: 市场（0=深圳, 1=上海）
            start: 起始位置
            
        Returns:
            股票列表
        """
        if not self.api:
            return []
        
        try:
            data = self.api.get_security_list(market, start)
            return data if data else []
        except Exception as e:
            logger.error(f"获取股票列表失败: {e}")
            return []
    
    def get_security_bars(self, market: int, code: str, start: int = 0, count: int = 800) -> pd.DataFrame:
        """获取K线数据
        
        Args:
            market: 市场（0=深圳, 1=上海）
            code: 股票代码
            start: 起始位置
            count: 数量
            
        Returns:
            K线DataFrame
        """
        if not self.api:
            return pd.DataFrame()
        
        try:
            data = self.api.get_security_bars(9, market, code, start, count)  # 9=日K
            
            if not data:
                return pd.DataFrame()
            
            df = pd.DataFrame(data)
            
            # 标准化字段
            df['trade_date'] = df['datetime'].apply(lambda x: x.split(' ')[0].replace('-', '').replace('/', ''))
            df = df.rename(columns={
                'open': 'open',
                'high': 'high',
                'low': 'low',
                'close': 'close',
                'vol': 'volume',
                'amount': 'amount'
            })
            
            return df
            
        except Exception as e:
            logger.error(f"获取K线失败: {code}, {e}")
            return pd.DataFrame()


# 工厂函数
def create_tdx_loader(local: bool = True, tdx_path: str = None) -> TdxLocalLoader:
    """创建通达信数据加载器
    
    Args:
        local: 是否使用本地数据
        tdx_path: 通达信路径
        
    Returns:
        数据加载器实例
    """
    if local:
        return TdxLocalLoader(tdx_path)
    else:
        return TdxOnlineLoader()