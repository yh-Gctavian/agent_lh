# -*- coding: utf-8 -*-
"""Factor base class"""

from abc import ABC, abstractmethod
from typing import Dict, Any
import pandas as pd


class Factor(ABC):
    """Factor base class"""
    
    def __init__(self, params: Dict[str, Any] = None):
        self.params = params or {}
        self.name = self.__class__.__name__
    
    @abstractmethod
    def calculate(self, data: pd.DataFrame) -> pd.Series:
        """Calculate factor value"""
        pass
    
    @property
    @abstractmethod
    def weight(self) -> float:
        """Factor weight"""
        pass
    
    def validate_data(self, data: pd.DataFrame) -> bool:
        """Validate input data"""
        required_cols = ['open', 'high', 'low', 'close', 'volume']
        return all(col in data.columns for col in required_cols)