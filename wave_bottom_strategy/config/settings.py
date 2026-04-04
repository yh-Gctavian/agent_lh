# -*- coding: utf-8 -*-
"""全局配置"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional


@dataclass
class Settings:
    """全局配置类"""
    
    # 项目路径
    project_root: Path = field(default_factory=lambda: Path(__file__).parent.parent.parent.parent)
    
    # 数据路径
    data_dir: Path = field(default_factory=lambda: Path("data"))
    cache_dir: Path = field(default_factory=lambda: Path("data/cache"))
    raw_dir: Path = field(default_factory=lambda: Path("data/raw"))
    adjusted_dir: Path = field(default_factory=lambda: Path("data/adjusted"))
    
    # 数据源配置
    data_source: str = "akshare"  # akshare / tushare
    
    # 回测配置
    backtest_start: str = "2020-01-01"
    backtest_end: str = "2025-12-31"
    benchmark: str = "000300"  # 沪深300 (AKShare格式)
    
    # 初始资金
    initial_capital: float = 1_000_000.0
    
    # 股票池
    stock_pool: List[str] = field(default_factory=lambda: ["hs300"])  # 沪深300成分股
    
    # 日志配置
    log_level: str = "INFO"
    log_file: str = "logs/wave_bottom.log"
    
    # 并行配置
    n_jobs: int = 4
    
    def __post_init__(self):
        """初始化后处理路径"""
        # 确保路径是绝对路径
        if not self.project_root.is_absolute():
            self.project_root = Path.cwd() / self.project_root
        
        # 转换为绝对路径
        self.data_dir = self.project_root / "data"
        self.cache_dir = self.data_dir / "cache"
        self.raw_dir = self.data_dir / "raw"
        self.adjusted_dir = self.data_dir / "adjusted"
        
        # 创建目录
        for d in [self.data_dir, self.cache_dir, self.raw_dir, self.adjusted_dir]:
            d.mkdir(parents=True, exist_ok=True)


# 全局单例
settings = Settings()