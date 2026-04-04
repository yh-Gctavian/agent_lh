# -*- coding: utf-8 -*-
"""修复导入路径脚本"""

import os
import re

# 需要修复的目录
BASE_DIR = 'wave_bottom_strategy'

# 导入映射规则
IMPORT_FIXES = [
    # 相对导入 -> 绝对导入
    (r'from \.\.utils\.logger import', 'from wave_bottom_strategy.utils.logger import'),
    (r'from \.\.selector\.engine import', 'from wave_bottom_strategy.selector.engine import'),
    (r'from \.\.data\.loader import', 'from wave_bottom_strategy.data.loader import'),
    
    # 短路径 -> 完整路径
    (r'from utils\.logger import', 'from wave_bottom_strategy.utils.logger import'),
    (r'from data\.loader import', 'from wave_bottom_strategy.data.loader import'),
    (r'from data\.processor import', 'from wave_bottom_strategy.data.processor import'),
    (r'from data\.cache import', 'from wave_bottom_strategy.data.cache import'),
    (r'from selector\.engine import', 'from wave_bottom_strategy.selector.engine import'),
    (r'from selector\.scorer import', 'from wave_bottom_strategy.selector.scorer import'),
    (r'from selector\.filter import', 'from wave_bottom_strategy.selector.filter import'),
    (r'from selector\.signal import', 'from wave_bottom_strategy.selector.signal import'),
    (r'from backtest\.engine import', 'from wave_bottom_strategy.backtest.engine import'),
    (r'from backtest\.portfolio import', 'from wave_bottom_strategy.backtest.portfolio import'),
    (r'from backtest\.matcher import', 'from wave_bottom_strategy.backtest.matcher import'),
    (r'from backtest\.benchmark import', 'from wave_bottom_strategy.backtest.benchmark import'),
    (r'from backtest\.metrics import', 'from wave_bottom_strategy.backtest.metrics import'),
    (r'from analysis\.metrics import', 'from wave_bottom_strategy.analysis.metrics import'),
    (r'from analysis\.layering import', 'from wave_bottom_strategy.analysis.layering import'),
    (r'from analysis\.sensitivity import', 'from wave_bottom_strategy.analysis.sensitivity import'),
    (r'from analysis\.reporter import', 'from wave_bottom_strategy.analysis.reporter import'),
    (r'from factors import', 'from wave_bottom_strategy.factors import'),
    (r'from factors\.kdj import', 'from wave_bottom_strategy.factors.kdj import'),
    (r'from factors\.ma import', 'from wave_bottom_strategy.factors.ma import'),
    (r'from factors\.volume import', 'from wave_bottom_strategy.factors.volume import'),
    (r'from factors\.rsi import', 'from wave_bottom_strategy.factors.rsi import'),
    (r'from factors\.macd import', 'from wave_bottom_strategy.factors.macd import'),
    (r'from factors\.bollinger import', 'from wave_bottom_strategy.factors.bollinger import'),
    (r'from factors\.base import', 'from wave_bottom_strategy.factors.base import'),
    (r'from config import', 'from wave_bottom_strategy.config import'),
    (r'from optimize\.param_optimizer import', 'from wave_bottom_strategy.optimize.param_optimizer import'),
    (r'from optimize\.grid_search import', 'from wave_bottom_strategy.optimize.grid_search import'),
    (r'from optimize\.sensitivity import', 'from wave_bottom_strategy.optimize.sensitivity import'),
    (r'from optimize\.walk_forward import', 'from wave_bottom_strategy.optimize.walk_forward import'),
]

def fix_file(filepath):
    """修复单个文件"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except UnicodeDecodeError:
        try:
            with open(filepath, 'r', encoding='gbk') as f:
                content = f.read()
        except:
            print(f"Skip: {filepath} (encoding error)")
            return False
    
    original = content
    for pattern, replacement in IMPORT_FIXES:
        content = re.sub(pattern, replacement, content)
    
    if content != original:
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Fixed: {filepath}")
            return True
        except Exception as e:
            print(f"Error writing {filepath}: {e}")
            return False
    return False

def main():
    """主函数"""
    fixed_count = 0
    
    for root, dirs, files in os.walk(BASE_DIR):
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                if fix_file(filepath):
                    fixed_count += 1
    
    print(f"\nTotal fixed: {fixed_count} files")

if __name__ == '__main__':
    main()