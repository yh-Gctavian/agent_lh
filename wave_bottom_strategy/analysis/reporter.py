# -*- coding: utf-8 -*-
"""报告生成器"""

from typing import Dict, Optional
from pathlib import Path
import pandas as pd
from datetime import datetime

from ..utils.logger import get_logger

logger = get_logger('report_generator')


class ReportGenerator:
    """报告生成器
    
    生成回测分析报告（Markdown格式）
    """
    
    def __init__(self, output_dir: Path = None):
        self.output_dir = output_dir or Path('reports')
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def generate(
        self,
        metrics: Dict,
        daily_values: pd.DataFrame,
        layer_result: pd.DataFrame = None,
        sensitivity_result: pd.DataFrame = None
    ) -> Path:
        """生成完整报告
        
        Args:
            metrics: 绩效指标
            daily_values: 每日净值
            layer_result: 分层分析结果
            sensitivity_result: 敏感性分析结果
            
        Returns:
            报告文件路径
        """
        content = self._build_report(
            metrics, daily_values, layer_result, sensitivity_result
        )
        
        filename = f"backtest_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        filepath = self.output_dir / filename
        
        filepath.write_text(content, encoding='utf-8')
        logger.info(f"报告已生成: {filepath}")
        
        return filepath
    
    def _build_report(
        self,
        metrics: Dict,
        daily_values: pd.DataFrame,
        layer_result: pd.DataFrame,
        sensitivity_result: pd.DataFrame
    ) -> str:
        """构建报告内容"""
        lines = [
            "# 波段抄底策略回测报告",
            "",
            f"生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "---",
            "",
            "## 一、绩效指标",
            "",
            "### 1.1 收益指标",
            "",
            "| 指标 | 值 |",
            "|------|------|",
            f"| 总收益率 | {metrics.get('total_return', 0)*100:.2f}% |",
            f"| 年化收益率 | {metrics.get('annual_return', 0)*100:.2f}% |",
            "",
            "### 1.2 风险指标",
            "",
            "| 指标 | 值 |",
            "|------|------|",
            f"| 最大回撤 | {metrics.get('max_drawdown', 0)*100:.2f}% |",
            f"| 年化波动率 | {metrics.get('volatility', 0)*100:.2f}% |",
            "",
            "### 1.3 风险调整收益",
            "",
            "| 指标 | 值 |",
            "|------|------|",
            f"| 夏普比率 | {metrics.get('sharpe_ratio', 0):.2f} |",
            f"| 卡玛比率 | {metrics.get('calmar_ratio', 0):.2f} |",
            f"| 索提诺比率 | {metrics.get('sortino_ratio', 0):.2f} |",
            "",
            "### 1.4 交易统计",
            "",
            "| 指标 | 值 |",
            "|------|------|",
            f"| 交易次数 | {metrics.get('trade_count', 0)} |",
            f"| 胜率 | {metrics.get('win_rate', 0)*100:.1f}% |",
            f"| 盈亏比 | {metrics.get('profit_loss_ratio', 0):.2f} |",
            "",
            "---",
            "",
        ]
        
        # 年度收益
        if layer_result is not None and not layer_result.empty:
            lines.extend([
                "## 二、年度收益分析",
                "",
                "| 年份 | 总收益率 | 最大回撤 | 波动率 |",
                "|------|---------|---------|--------|",
            ])
            
            for _, row in layer_result.iterrows():
                lines.append(
                    f"| {int(row['year'])} | {row['total_return']*100:.2f}% | "
                    f"{row['max_drawdown']*100:.2f}% | {row['volatility']*100:.2f}% |"
                )
            
            lines.extend(["", "---", ""])
        
        # 参数优化
        if sensitivity_result is not None and not sensitivity_result.empty:
            lines.extend([
                "## 三、最优参数组合",
                "",
                "基于夏普比率排序Top5：",
                "",
                "| 排名 | 参数组合 | 夏普比率 | 总收益率 |",
                "|------|---------|---------|---------|",
            ])
            
            for i, (_, row) in enumerate(sensitivity_result.head(5).iterrows()):
                lines.append(
                    f"| {i+1} | - | {row.get('sharpe_ratio', 0):.2f} | "
                    f"{row.get('total_return', 0)*100:.2f}% |"
                )
            
            lines.extend(["", "---", ""])
        
        # 收益曲线说明
        lines.extend([
            "## 四、收益曲线",
            "",
            "（收益曲线图待可视化模块生成）",
            "",
            "---",
            "",
            "## 五、结论与建议",
            "",
            "### 5.1 策略评价",
            "",
            "根据回测结果，策略表现如下：",
            "",
        ])
        
        sharpe = metrics.get('sharpe_ratio', 0)
        if sharpe > 1:
            lines.append("- 夏普比率 > 1，策略风险调整收益良好")
        elif sharpe > 0.5:
            lines.append("- 夏普比率在0.5-1之间，策略表现一般")
        else:
            lines.append("- 夏普比率 < 0.5，策略需要优化")
        
        max_dd = abs(metrics.get('max_drawdown', 0))
        if max_dd < 0.1:
            lines.append("- 最大回撤 < 10%，风险控制良好")
        elif max_dd < 0.2:
            lines.append("- 最大回撤在10%-20%，风险适中")
        else:
            lines.append("- 最大回撤 > 20%，风险较高")
        
        lines.extend([
            "",
            "### 5.2 优化建议",
            "",
            "1. 可调整因子权重优化选股效果",
            "2. 可通过参数敏感性分析寻找最优参数",
            "3. 建议进行Walk-Forward验证避免过拟合",
            "",
            "---",
            "",
            f"*报告生成于 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*",
        ])
        
        return "\n".join(lines)
    
    def generate_summary(self, metrics: Dict) -> str:
        """生成简要摘要
        
        Args:
            metrics: 绩效指标
            
        Returns:
            摘要文本
        """
        return f"""
=== 回测结果摘要 ===

年化收益: {metrics.get('annual_return', 0)*100:.2f}%
最大回撤: {metrics.get('max_drawdown', 0)*100:.2f}%
夏普比率: {metrics.get('sharpe_ratio', 0):.2f}
胜率: {metrics.get('win_rate', 0)*100:.1f}%
盈亏比: {metrics.get('profit_loss_ratio', 0):.2f}
"""
    
    def generate_optimal_params_report(
        self,
        optimal_params: Dict,
        backtest_result: Dict
    ) -> str:
        """生成最优参数推荐报告
        
        Args:
            optimal_params: 最优参数
            backtest_result: 回测结果
            
        Returns:
            报告文本
        """
        lines = [
            "# 最优参数推荐报告",
            "",
            f"生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "---",
            "",
            "## 一、推荐参数组合",
            "",
            "### 1.1 核心参数",
            "",
            "| 参数 | 推荐值 | 说明 |",
            "|------|--------|------|",
        ]
        
        # 参数说明
        param_desc = {
            'min_score': '最低选股得分阈值',
            'max_positions': '最大持仓数量',
            'single_position_pct': '单票仓位比例',
            'rebalance_freq': '调仓频率（天）',
            'kdj_j_threshold': 'KDJ J值超卖阈值',
            'stop_profit': '止盈比例',
            'stop_loss': '止损比例'
        }
        
        for param, value in optimal_params.items():
            desc = param_desc.get(param, '-')
            if isinstance(value, float):
                lines.append(f"| {param} | {value:.2f} | {desc} |")
            else:
                lines.append(f"| {param} | {value} | {desc} |")
        
        lines.extend([
            "",
            "### 1.2 参数优化方法",
            "",
            "- 敏感性分析：单参数影响评估",
            "- 网格搜索：多参数组合优化",
            "- Walk-Forward验证：样本外验证防止过拟合",
            "",
            "---",
            "",
            "## 二、回测验证结果",
            "",
            "| 指标 | 训练集(2020-2023) | 测试集(2024-2025) |",
            "|------|------------------|------------------|",
        ])
        
        # 假设有训练集和测试集结果
        if 'train_metrics' in backtest_result:
            train = backtest_result['train_metrics']
            test = backtest_result.get('test_metrics', {})
            lines.append(f"| 年化收益 | {train.get('annual_return', 0)*100:.2f}% | {test.get('annual_return', 0)*100:.2f}% |")
            lines.append(f"| 夏普比率 | {train.get('sharpe_ratio', 0):.2f} | {test.get('sharpe_ratio', 0):.2f} |")
            lines.append(f"| 最大回撤 | {train.get('max_drawdown', 0)*100:.2f}% | {test.get('max_drawdown', 0)*100:.2f}% |")
        
        return "\n".join(lines)
    
    def generate_capital_suggestion(
        self,
        metrics: Dict,
        risk_tolerance: str = 'moderate'
    ) -> str:
        """生成资金规模建议
        
        Args:
            metrics: 绩效指标
            risk_tolerance: 风险偏好（conservative/moderate/aggressive）
            
        Returns:
            资金建议文本
        """
        max_dd = abs(metrics.get('max_drawdown', 0.15))
        sharpe = metrics.get('sharpe_ratio', 0.5)
        
        lines = [
            "# 资金规模建议",
            "",
            f"生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "---",
            "",
            "## 一、风险评估",
            "",
            f"- 历史最大回撤：{max_dd*100:.2f}%",
            f"- 夏普比率：{sharpe:.2f}",
            f"- 风险偏好：{risk_tolerance}",
            "",
            "## 二、资金建议",
            "",
        ]
        
        # 根据风险偏好和回撤计算建议资金
        if risk_tolerance == 'conservative':
            # 保守型：最大回撤不超过本金的5%
            suggested_capital = 50000 / max_dd if max_dd > 0 else 100000
            max_loss = suggested_capital * max_dd
            lines.extend([
                f"### 保守型投资者",
                "",
                f"- 建议初始资金：{suggested_capital:.0f} 元",
                f"- 预期最大亏损：{max_loss:.0f} 元",
                f"- 风险承受：最大亏损不超过本金5%",
                "",
            ])
        elif risk_tolerance == 'aggressive':
            # 激进型：最大回撤不超过本金的20%
            suggested_capital = 200000 / max_dd if max_dd > 0 else 500000
            max_loss = suggested_capital * max_dd
            lines.extend([
                f"### 激进型投资者",
                "",
                f"- 建议初始资金：{suggested_capital:.0f} 元",
                f"- 预期最大亏损：{max_loss:.0f} 元",
                f"- 风险承受：最大亏损不超过本金20%",
                "",
            ])
        else:
            # 稳健型
            suggested_capital = 100000 / max_dd if max_dd > 0 else 200000
            max_loss = suggested_capital * max_dd
            lines.extend([
                f"### 稳健型投资者",
                "",
                f"- 建议初始资金：{suggested_capital:.0f} 元",
                f"- 预期最大亏损：{max_loss:.0f} 元",
                f"- 风险承受：最大亏损不超过本金10%",
                "",
            ])
        
        lines.extend([
            "---",
            "",
            "## 三、仓位管理建议",
            "",
            "- 单票最大仓位：10%",
            "- 最大持仓数：10只",
            "- 总仓位上限：80%",
            "- 现金保留：至少20%应对风险",
            "",
            "## 四、风险提示",
            "",
            "1. 历史业绩不代表未来表现",
            "2. 策略可能存在过拟合风险",
            "3. 市场极端情况下可能产生更大回撤",
            "4. 建议分批入场，控制初始仓位",
            "",
            f"*报告生成于 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*",
        ])
        
        return "\n".join(lines)