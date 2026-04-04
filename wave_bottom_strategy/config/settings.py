# -*- coding: utf-8 -*-
"""Global settings"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import List


@dataclass
class Settings:
    """Global settings"""
    project_root: Path = field(default_factory=lambda: Path("."))
    data_dir: Path = field(default_factory=lambda: Path("data"))
    backtest_start: str = "2020-01-01"
    backtest_end: str = "2025-12-31"
    benchmark: str = "000300.SH"
    initial_capital: float = 1000000.0
    log_level: str = "INFO"
    stock_pool: List[str] = field(default_factory=list)


settings = Settings()