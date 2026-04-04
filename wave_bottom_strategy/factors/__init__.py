# -*- coding: utf-8 -*-
"""因子模块"""

from .base import Factor
from .kdj import KDJFactor
from .ma import MAFactor
from .volume import VolumeFactor
from .rsi import RSIFactor
from .macd import MACDFactor
from .bollinger import BollingerFactor
from .registry import FactorRegistry

__all__ = [
    'Factor',
    'KDJFactor',
    'MAFactor',
    'VolumeFactor',
    'RSIFactor',
    'MACDFactor',
    'BollingerFactor',
    'FactorRegistry',
]
