# -*- coding: utf-8 -*-
"""通用工具函数"""

from pathlib import Path
import re


def normalize_code(code: str) -> str:
    """标准化股票代码格式
    
    Args:
        code: 原始代码（如 000001 或 000001.SZ）
        
    Returns:
        标准化代码（如 000001.SZ）
    """
    code = code.strip()
    
    # 已有后缀
    if '.' in code:
        return code
    
    # 根据代码推断市场
    if code.startswith('6'):
        return f"{code}.SH"
    elif code.startswith(('0', '3')):
        return f"{code}.SZ"
    elif code.startswith('68'):
        return f"{code}.SH"  # 科创板
    else:
        return f"{code}.SZ"  # 默认深市


def ensure_dir(path: Path) -> Path:
    """确保目录存在
    
    Args:
        path: 目录路径
        
    Returns:
        目录路径
    """
    path.mkdir(parents=True, exist_ok=True)
    return path


def parse_date(date_str: str) -> str:
    """解析日期字符串
    
    Args:
        date_str: 日期字符串（各种格式）
        
    Returns:
        标准格式 YYYY-MM-DD
    """
    # 支持多种格式：YYYYMMDD, YYYY-MM-DD, YYYY/MM/DD
    pattern = r'(\d{4})[-/]?(\d{2})[-/]?(\d{2})'
    match = re.match(pattern, date_str)
    if match:
        return f"{match.group(1)}-{match.group(2)}-{match.group(3)}"
    return date_str