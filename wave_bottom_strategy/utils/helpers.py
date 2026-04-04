# -*- coding: utf-8 -*-
"""通用工具函数"""

from pathlib import Path
import re


def normalize_code(code: str) -> str:
    """标准化股票代码格式"""
    code = code.strip()
    if '.' in code:
        return code
    if code.startswith('6'):
        return f"{code}.SH"
    elif code.startswith(('0', '3')):
        return f"{code}.SZ"
    else:
        return f"{code}.SZ"


def ensure_dir(path: Path) -> Path:
    """确保目录存在"""
    path.mkdir(parents=True, exist_ok=True)
    return path


def parse_date(date_str: str) -> str:
    """解析日期字符串"""
    pattern = r'(\d{4})[-/]?(\d{2})[-/]?(\d{2})'
    match = re.match(pattern, date_str)
    if match:
        return f"{match.group(1)}-{match.group(2)}-{match.group(3)}"
    return date_str