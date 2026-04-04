# -*- coding: utf-8 -*-
"""全局配置"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Literal


@dataclass
class BacktestConfig:
    """回测配置"""
    
    # 交易成本
    commission_rate: float = 0.0003  # 佣金费率 0.03%
    min_commission: float = 5.0  # 最低佣金 5元
    stamp_duty_rate: float = 0.001  # 印花税 0.1%（仅卖出）
    transfer_fee_rate: float = 0.00001  # 过户费 0.001%
    slippage_rate: float = 0.001  # 滑点 0.1%
    
    # 仓位管理
    max_positions: int = 10  # 最大持仓数量
    position_size: float = 0.1  # 单只股票仓位比例（等权模式）
    position_mode: Literal['equal', 'score_weighted'] = 'equal'  # 仓位模式
    
    # 调仓规则
    rebalance_freq: int = 5  # 调仓频率（交易日）
    min_score: float = 60.0  # 最低选股得分
    
    # 止盈止损
    enable_stop_loss: bool = False  # 是否启用止损
    stop_loss_pct: float = 0.05  # 止损比例 5%
    enable_take_profit: bool = False  # 是否启用止盈
    take_profit_pct: float = 0.10  # 止盈比例 10%
    max_holding_days: int = 20  # 最大持仓天数


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
    result_dir: Path = field(default_factory=lambda: Path("data/results"))
    
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
    
    # 回测详细配置
    backtest: BacktestConfig = field(default_factory=BacktestConfig)
    
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
        self.result_dir = self.data_dir / "results"
        
        # 创建目录
        for d in [self.data_dir, self.cache_dir, self.raw_dir, self.adjusted_dir, self.result_dir]:
            d.mkdir(parents=True, exist_ok=True)


# 全局单例
settings = Settings()