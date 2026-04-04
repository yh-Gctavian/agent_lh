# -*- coding: utf-8 -*-
"""
波段抄底策略选股系统安装配置
"""

from setuptools import setup, find_packages

setup(
    name='wave_bottom_strategy',
    version='1.0.0',
    description='波段抄底策略选股系统 - 多因子量化选股与回测框架',
    author='量化开发经理 (KkTTM7)',
    packages=find_packages(),
    install_requires=[
        'pandas>=1.5.0',
        'numpy>=1.21.0',
        'akshare>=1.10.0',
        'matplotlib>=3.5.0',
        'plotly>=5.10.0',
        'pyarrow>=8.0.0',
    ],
    python_requires='>=3.8',
)