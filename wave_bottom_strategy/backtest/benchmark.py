# -*- coding: utf-8 -*-
"""基准对比"""

import pandas as pd
import logging

logger = logging.getLogger('benchmark')


class Benchmark:
    """基准对比 - 沪深300"""
    
    def __init__(self, code: str = "000300"):
        self.code = code
        self.data = None
    
    def load_data(self, start: str, end: str):
        """加载基准数据"""
        try:
            import akshare as ak
            self.data = ak.stock_zh_index_daily(symbol=f"sh{self.code}")
            logger.info("基准数据加载完成")
        except Exception as e:
            logger.warning(f"基准数据加载失败: {e}")