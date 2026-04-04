# -*- coding: utf-8 -*-
"""联调测试脚本"""

from wave_bottom_strategy.main import run_backtest, run_parameter_optimization, generate_final_report
from utils.logger import get_logger

logger = get_logger('integration_test')


def test_integration():
    """联调测试"""
    logger.info("=" * 60)
    logger.info("M6 联调测试开始")
    logger.info("=" * 60)
    
    try:
        # 1. 测试回测流程
        logger.info("\n[1/3] 测试回测流程...")
        backtest_result = run_backtest(
            start_date='2024-01-01',
            end_date='2024-12-31',
            initial_capital=1000000
        )
        logger.info("✅ 回测流程正常")
        
        # 2. 测试参数优化
        logger.info("\n[2/3] 测试参数优化...")
        optimization_result = run_parameter_optimization(
            start_date='2020-01-01',
            end_date='2025-12-31'
        )
        logger.info("✅ 参数优化正常")
        
        # 3. 生成最终报告
        logger.info("\n[3/3] 生成最终报告...")
        report_path = generate_final_report(backtest_result, optimization_result)
        logger.info(f"✅ 报告已生成: {report_path}")
        
        logger.info("\n" + "=" * 60)
        logger.info("M6 联调测试通过！")
        logger.info("=" * 60)
        
        return True
        
    except Exception as e:
        logger.error(f"联调测试失败: {e}")
        return False


if __name__ == '__main__':
    test_integration()