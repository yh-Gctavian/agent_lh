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