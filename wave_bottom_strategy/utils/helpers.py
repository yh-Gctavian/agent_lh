# -*- coding: utf-8 -*-
"""Helper utilities"""

from pathlib import Path


def normalize_code(code: str) -> str:
    """Normalize stock code format"""
    code = code.strip()
    if '.' in code:
        return code
    if code.startswith('6'):
        return "%s.SH" % code
    elif code.startswith(('0', '3')):
        return "%s.SZ" % code
    else:
        return "%s.SZ" % code


def ensure_dir(path: Path) -> Path:
    """Ensure directory exists"""
    path.mkdir(parents=True, exist_ok=True)
    return path