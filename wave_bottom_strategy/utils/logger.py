# -*- coding: utf-8 -*-
"""日志工具"""

import logging
from pathlib import Path


def get_logger(
    name: str = 'wave_bottom',
    level: str = 'INFO',
    log_file: str = None
) -> logging.Logger:
    """获取日志�?
    
    Args:
        name: 日志器名�?
        level: 日志级别
        log_file: 日志文件路径
        
    Returns:
        Logger实例
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    if not logger.handlers:
        # 控制台输�?
        console = logging.StreamHandler()
        console.setLevel(level)
        formatter = logging.Formatter(
            '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        )
        console.setFormatter(formatter)
        logger.addHandler(console)
        
        # 文件输出
        if log_file:
            Path(log_file).parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setLevel(level)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
    
    return logger
