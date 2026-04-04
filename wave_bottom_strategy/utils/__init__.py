# -*- coding: utf-8 -*-
"""工具模块

支持两种导入方式：
1. 作为包导入: from wave_bottom_strategy.utils.logger import get_logger
2. 相对导入: from utils.logger import get_logger
"""

import sys
from pathlib import Path

# 确保项目根目录在路径中
_project_root = Path(__file__).parent.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from .logger import get_logger
from .calendar import TradeCalendar
from .helpers import normalize_code, ensure_dir

__all__ = ['get_logger', 'TradeCalendar', 'normalize_code', 'ensure_dir']