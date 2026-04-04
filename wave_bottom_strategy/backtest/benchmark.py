# -*- coding: utf-8 -*-
"""Benchmark comparison"""

import pandas as pd
import logging

logger = logging.getLogger('benchmark')


class Benchmark:
    """Benchmark - CSI 300"""
    
    def __init__(self, code: str = "000300"):
        self.code = code
        self.data = None
    
    def load_data(self, start: str, end: str):
        """Load benchmark data"""
        try:
            import akshare as ak
            self.data = ak.stock_zh_index_daily(symbol="sh%s" % self.code)
            logger.info("Benchmark data loaded")
        except Exception as e:
            logger.warning("Failed to load benchmark: %s" % e)