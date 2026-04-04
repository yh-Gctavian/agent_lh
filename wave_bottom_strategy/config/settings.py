# -*- coding: utf-8 -*-
"""全局配置"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import List


@dataclass
class Settings:
    """全局配置类"""
    
    # 项目路径
    project_root: Path = field(default_factory=lambda: Path(__file__).parent.parent.parent)
    
    # 数据路径
    data_dir: Path = field(default_factory=lambda: Path("data"))
    cache_dir: Path = field(default_factory=lambda: Path("data/cache"))
    
    # 回测配置
    backtest_start: str = "2020-01-01"
    backtest_end: str = "2025-12-31"
    benchmark: str = "000300.SH"  # 沪深300
    
    # 初始资金
    initial_capital: float = 1_000_000.0
    
    # 股票池
    stock_pool: List[str] = field(default_factory=lambda: ["000300.SH"])  # 沪深300成分股
    
    # 日志配置
    log_level: str = "INFO"
    log_file: str = "logs/wave_bottom.log"


settings = Settings()