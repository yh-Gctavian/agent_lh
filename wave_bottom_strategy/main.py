# -*- coding: utf-8 -*-
"""波段抄底策略主入口"""

import argparse
from pathlib import Path

from config import settings, FACTOR_PARAMS, SELECTOR_PARAMS
from wave_bottom_strategy.utils.logger import get_logger


logger = get_logger('wave_bottom', settings.log_level, settings.log_file)


def run_backtest(start_date: str, end_date: str):
    """运行回测
    
    Args:
        start_date: 开始日期
        end_date: 结束日期
    """
    logger.info(f"开始回测: {start_date} -> {end_date}")
    
    # TODO: 实现回测流程
    # 1. 加载数据
    # 2. 计算因子
    # 3. 选股
    # 4. 回测
    # 5. 分析
    # 6. 生成报告
    
    logger.info("回测完成")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='波段抄底策略')
    parser.add_argument('--mode', choices=['backtest', 'select'], default='backtest',
                        help='运行模式: backtest(回测) / select(选股)')
    parser.add_argument('--start', default=settings.backtest_start,
                        help='开始日期 (YYYY-MM-DD)')
    parser.add_argument('--end', default=settings.backtest_end,
                        help='结束日期 (YYYY-MM-DD)')
    
    args = parser.parse_args()
    
    if args.mode == 'backtest':
        run_backtest(args.start, args.end)
    else:
        logger.info("选股模式待实现")


if __name__ == '__main__':
    main()