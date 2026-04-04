# -*- coding: utf-8 -*-
"""因子注册中心"""

from typing import Dict, Type, List
from .base import Factor


class FactorRegistry:
    """因子注册中心"""
    
    _factors: Dict[str, Type[Factor]] = {}
    
    @classmethod
    def register(cls, factor_class: Type[Factor]):
        name = factor_class.__name__
        cls._factors[name] = factor_class
    
    @classmethod
    def get(cls, name: str, params: dict = None) -> Factor:
        if name not in cls._factors:
            raise ValueError(f"Factor '{name}' not registered")
        return cls._factors[name](params)
    
    @classmethod
    def list_all(cls) -> List[str]:
        return list(cls._factors.keys())