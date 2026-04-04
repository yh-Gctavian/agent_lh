# -*- coding: utf-8 -*-
"""日志工具"""

import logging
from pathlib import Path


def get_logger(name: str = 'wave_bottom', level: str = 'INFO', log_file: str = None) -> logging.Logger:
    """获取日志器"""
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    if not logger.handlers:
        console = logging.StreamHandler()
        console.setLevel(level)
        formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(name)s: %(message)s')
        console.setFormatter(formatter)
        logger.addHandler(console)
        
        if log_file:
            Path(log_file).parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setLevel(level)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
    
    return logger