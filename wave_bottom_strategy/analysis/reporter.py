# -*- coding: utf-8 -*-
"""报告生成器"""

from typing import Dict, Optional
from pathlib import Path
from datetime import datetime
import pandas as pd

from utils.logger import get_logger

logger = get_logger('report_generator')


class ReportGenerator:
    """报告生成器"""
    
    def __init__(self, output_dir: Path = None):
        self.output_dir = output_dir or Path('reports')
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def generate(
        self,
        metrics: Dict,
        backtest_result: Dict,
        layer_result: pd.DataFrame = None,
        sensitivity_result: pd.DataFrame = None,
        filename: str = None
    ) -> Path:
        """生成报告"""
        if filename is None:
            filename = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        
        content = self._build_markdown(
            metrics, backtest_result, layer_result, sensitivity_result
        )
        
        filepath = self.output_dir / filename
        filepath.write_text(content, encoding='utf-8')
        
        logger.info(f"报告生成: {filepath}")
        return filepath
    
    def _build_markdown(
        self,
        metrics: Dict,
        backtest_result: Dict,
        layer_result: pd.DataFrame,
        sensitivity_result: pd.DataFrame
    ) -> str:
        """构建Markdown报告"""
        lines = [
            "# 波段抄底策略回测报告",
            "",
            f"生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "---",
            "",
            "## 一、绩效指标",
            "",
            "| 指标 | 值 |",
            "|------|------|",
        ]
        
        for key, value in metrics.items():
            if isinstance(value, float):
                lines.append(f"| {key} | {value:.4f} |")
            else:
                lines.append(f"| {key} | {value} |")
        
        # 回测概览
        lines.extend([
            "",
            "## 二、回测概览",
            "",
            f"- 初始资金: {backtest_result.get('initial', 'N/A'):,.0f}",
            f"- 最终净值: {backtest_result.get('final', 'N/A'):,.0f}",
            f"- 总收益率: {backtest_result.get('total_return', 0)*100:.2f}%",
            f"- 交易次数: {backtest_result.get('trades', 0)}",
            "",
        ])
        
        # 分层分析
        if layer_result is not None and not layer_result.empty:
            lines.extend([
                "## 三、分层分析",
                "",
                layer_result.to_markdown(index=False),
                "",
            ])
        
        # 敏感性分析
        if sensitivity_result is not None and not sensitivity_result.empty:
            lines.extend([
                "## 四、参数敏感性分析",
                "",
                sensitivity_result.to_markdown(index=False),
                "",
            ])
        
        # 风险提示
        lines.extend([
            "---",
            "",
            "## 风险提示",
            "",
            "- 历史表现不代表未来收益",
            "- 本策略仅供研究参考，不构成投资建议",
            "- 实盘交易需考虑滑点、冲击成本等因素",
            "",
        ])
        
        return "\n".join(lines)
    
    def generate_summary_table(
        self,
        results_list: List[Dict]
    ) -> pd.DataFrame:
        """生成汇总表"""
        return pd.DataFrame(results_list)