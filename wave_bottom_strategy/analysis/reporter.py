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
        daily_df: pd.DataFrame = None,
        layer_result: pd.DataFrame = None,
        sensitivity_result: pd.DataFrame = None
    ) -> Path:
        """生成报告"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"backtest_report_{timestamp}.md"
        filepath = self.output_dir / filename
        
        content = self._generate_markdown(metrics, daily_df, layer_result, sensitivity_result)
        filepath.write_text(content, encoding='utf-8')
        
        logger.info(f"报告已生成: {filepath}")
        return filepath
    
    def _generate_markdown(
        self,
        metrics: Dict,
        daily_df: pd.DataFrame,
        layer_result: pd.DataFrame,
        sensitivity_result: pd.DataFrame
    ) -> str:
        lines = [
            "# 波段抄底策略回测报告",
            "",
            f"生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## 一、绩效指标",
            "",
            "| 指标 | 值 |",
            "|------|------|",
        ]
        
        for key, value in metrics.items():
            lines.append(f"| {key} | {value} |")
        
        if layer_result is not None and not layer_result.empty:
            lines.extend([
                "",
                "## 二、分层分析",
                "",
                layer_result.to_markdown(index=False),
            ])
        
        if sensitivity_result is not None and not sensitivity_result.empty:
            lines.extend([
                "",
                "## 三、参数敏感性分析",
                "",
                sensitivity_result.to_markdown(index=False),
            ])
        
        lines.extend([
            "",
            "---",
            f"*报告生成于 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*"
        ])
        
        return "\n".join(lines)