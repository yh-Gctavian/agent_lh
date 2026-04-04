# -*- coding: utf-8 -*-
"""Global settings"""

from dataclasses import dataclass
from pathlib import Path


@dataclass
class Settings:
    """Global settings"""
    project_root: Path = None
    data_dir: Path = None
    backtest_start: str = "2020-01-01"
    backtest_end: str = "2025-12-31"
    benchmark: str = "000300.SH"
    initial_capital: float = 1000000.0
    log_level: str = "INFO"


settings = Settings()