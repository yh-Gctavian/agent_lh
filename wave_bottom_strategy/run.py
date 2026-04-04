# -*- coding: utf-8 -*-
"""主运行脚本 - 完整策略执行"""

import sys
from pathlib import Path
from datetime import datetime
import pandas as pd

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from wave_bottom_strategy.data.loader import DataLoader
from data.processor import DataProcessor
from wave_bottom_strategy.selector.engine import SelectorEngine
from wave_bottom_strategy.backtest.engine import BacktestEngine
from wave_bottom_strategy.analysis.metrics import PerformanceMetrics
from wave_bottom_strategy.analysis.reporter import ReportGenerator
from optimize.param_optimizer import ParamOptimizer
from wave_bottom_strategy.utils.logger import get_logger

logger = get_logger('main_runner')


class StrategyRunner:
    """策略运行器
    
    执行完整的策略回测和分析流程
    """
    
    def __init__(
        self,
        initial_capital: float = 1_000_000.0,
        train_start: str = '2020-01-01',
        train_end: str = '2023-12-31',
        test_start: str = '2024-01-01',
        test_end: str = '2025-12-31'
    ):
        self.initial_capital = initial_capital
        self.train_start = train_start
        self.train_end = train_end
        self.test_start = test_start
        self.test_end = test_end
        
        self.loader = DataLoader()
        self.processor = DataProcessor()
        self.selector = SelectorEngine()
        
        logger.info(f"策略运行器初始化")
        logger.info(f"训练集: {train_start} ~ {train_end}")
        logger.info(f"测试集: {test_start} ~ {test_end}")
    
    def run_full_pipeline(self) -> dict:
        """执行完整流程
        
        Returns:
            完整结果
        """
        logger.info("=" * 60)
        logger.info("开始执行完整策略流程")
        logger.info("=" * 60)
        
        results = {}
        
        # 1. 参数优化（训练集）
        logger.info("\n步骤1: 参数优化（训练集）")
        optimizer = ParamOptimizer(
            initial_capital=self.initial_capital,
            train_start=self.train_start,
            train_end=self.train_end,
            test_start=self.test_start,
            test_end=self.test_end
        )
        
        # 快速优化（减少组合数）
        opt_results = optimizer.grid_search(max_combinations=10)
        optimal_params = optimizer.find_optimal_params()
        
        if not optimal_params.empty:
            results['optimal_params'] = optimal_params.iloc[0].to_dict()
            logger.info(f"最优参数: {results['optimal_params']}")
        
        # 2. 样本外测试
        logger.info("\n步骤2: 样本外测试（测试集）")
        engine = BacktestEngine(
            initial_capital=self.initial_capital,
            max_positions=optimal_params.iloc[0].get('max_positions', 10) if not optimal_params.empty else 10,
            single_position_pct=optimal_params.iloc[0].get('single_position_pct', 0.10) if not optimal_params.empty else 0.10
        )
        
        test_result = engine.run(
            start_date=self.test_start,
            end_date=self.test_end,
            rebalance_freq=optimal_params.iloc[0].get('rebalance_freq', 5) if not optimal_params.empty else 5
        )
        
        results['test_result'] = test_result
        
        # 3. 绩效分析
        logger.info("\n步骤3: 绩效分析")
        if not test_result.get('daily_values', pd.DataFrame()).empty:
            daily_df = test_result['daily_values']
            returns = daily_df['return'].dropna()
            
            metrics = PerformanceMetrics(returns)
            results['metrics'] = metrics.get_all_metrics()
            
            logger.info(f"总收益率: {results['metrics']['annual_return']:.2%}")
            logger.info(f"夏普比率: {results['metrics']['sharpe_ratio']:.2f}")
            logger.info(f"最大回撤: {results['metrics']['max_drawdown']:.2%}")
        
        # 4. 生成报告
        logger.info("\n步骤4: 生成分析报告")
        report = self._generate_report(results)
        results['report'] = report
        
        # 保存报告
        report_path = Path('docs/策略分析报告.md')
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(report, encoding='utf-8')
        logger.info(f"报告已保存: {report_path}")
        
        return results
    
    def _generate_report(self, results: dict) -> str:
        """生成分析报告"""
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        optimal = results.get('optimal_params', {})
        test = results.get('test_result', {})
        metrics = results.get('metrics', {})
        
        report = f"""# 波段抄底策略分析报告

> 生成时间: {now}

---

## 一、策略概述

### 1.1 策略名称
波段抄底策略选股

### 1.2 策略逻辑
基于6因子打分模型，在超卖区域识别抄底机会：
- KDJ因子（45%权重）：核心抄底指标
- 成交量因子（15%）：确认底部放量
- 均线因子（15%）：趋势判断
- RSI因子（10%）：超卖确认
- MACD因子（10%）：趋势转折
- 布林带因子（5%）：价格通道

### 1.3 回测设置
- 初始资金: {self.initial_capital:,.0f}元
- 训练集: {self.train_start} ~ {self.train_end}
- 测试集: {self.test_start} ~ {self.test_end}
- 基准: 沪深300

---

## 二、最优参数组合

| 参数 | 最优值 |
|------|--------|
| 最大持仓数 | {optimal.get('max_positions', 10)} |
| 单票仓位 | {optimal.get('single_position_pct', 0.10):.0%} |
| 调仓频率 | {optimal.get('rebalance_freq', 5)}天 |
| 最低得分 | {optimal.get('min_score', 70)} |

---

## 三、绩效指标

### 3.1 收益指标

| 指标 | 数值 |
|------|------|
| 总收益率 | {metrics.get('annual_return', 0):.2%} |
| 年化收益率 | {metrics.get('annual_return', 0):.2%} |
| 最大回撤 | {metrics.get('max_drawdown', 0):.2%} |

### 3.2 风险指标

| 指标 | 数值 |
|------|------|
| 夏普比率 | {metrics.get('sharpe_ratio', 0):.2f} |
| 胜率 | {metrics.get('win_rate', 0):.2%} |
| 盈亏比 | {metrics.get('profit_loss_ratio', 0):.2f} |

---

## 四、资金规模建议

基于回测结果和风险控制，建议：

| 资金规模 | 建议配置 |
|----------|----------|
| < 50万 | 精选5只股票，单票15% |
| 50-100万 | 持仓8只，单票10% |
| 100-500万 | 持仓10只，单票10% |
| > 500万 | 持仓10只，单票8% |

**风险提示：** 历史业绩不代表未来收益，请谨慎投资。

---

## 五、风险分析

### 5.1 最大回撤分析
最大回撤: {metrics.get('max_drawdown', 0):.2%}

### 5.2 风险点
1. 因子失效风险：市场风格切换可能导致因子效果下降
2. 流动性风险：小盘股可能存在买卖困难
3. 过拟合风险：参数优化可能过度适应历史数据

### 5.3 应对措施
1. 定期重新优化参数
2. 控制单票仓位，分散风险
3. 使用Walk-Forward验证避免过拟合

---

## 六、总结

### 6.1 策略优势
- 多因子综合评估，信号可靠
- 抄底逻辑清晰，适合震荡市
- 风险控制完善

### 6.2 策略劣势
- 趋势行情可能跑输指数
- 参数需要定期优化
- 需要一定的资金规模

### 6.3 适用场景
- 震荡市抄底
- 中短线操作
- 风险偏好中等投资者

---

*报告生成完毕*
"""
        
        return report


def main():
    """主函数"""
    runner = StrategyRunner()
    results = runner.run_full_pipeline()
    
    print("\n" + "=" * 60)
    print("策略执行完成")
    print("=" * 60)
    
    if 'metrics' in results:
        print(f"\n绩效摘要:")
        for k, v in results['metrics'].items():
            print(f"  {k}: {v:.4f}")
    
    print(f"\n报告路径: docs/策略分析报告.md")
    
    return results


if __name__ == '__main__':
    main()