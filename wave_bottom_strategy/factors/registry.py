# -*- coding: utf-8 -*-
"""因子注册中心"""

from typing import Dict, Type, List
from .base import Factor


class FactorRegistry:
    """因子注册中心
    
    用于管理和获取所有因子实例
    """
    
    _factors: Dict[str, Type[Factor]] = {}
    
    @classmethod
    def register(cls, factor_class: Type[Factor]):
        """注册因子类
        
        Args:
            factor_class: 因子类
        """
        name = factor_class.__name__
        cls._factors[name] = factor_class
    
    @classmethod
    def get(cls, name: str, params: dict = None) -> Factor:
        """获取因子实例
        
        Args:
            name: 因子名称
            params: 因子参数
            
        Returns:
            因子实例
        """
        if name not in cls._factors:
            raise ValueError(f"Factor '{name}' not registered")
        return cls._factors[name](params)
    
    @classmethod
    def list_all(cls) -> List[str]:
        """列出所有已注册的因子名称
        
        Returns:
            因子名称列表
        """
        return list(cls._factors.keys())
    
    @classmethod
    def get_all_factors(cls, params_dict: Dict[str, dict] = None) -> List[Factor]:
        """获取所有因子实例
        
        Args:
            params_dict: 各因子的参数配置
            
        Returns:
            因子实例列表
        """
        params_dict = params_dict or {}
        factors = []
        for name in cls._factors:
            params = params_dict.get(name.lower().replace('factor', ''), {})
            factors.append(cls.get(name, params))
        return factors