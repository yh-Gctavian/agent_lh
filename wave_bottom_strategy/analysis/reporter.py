# -*- coding: utf-8 -*-
"""报告生成器"""

from typing import Dict, Optional
from pathlib import Path
from datetime import datetime
import pandas as pd

from utils.logger import get_logger

logger = get_logger('reporter')


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
        format: str = 'markdown'
    ) -> Path:
        """生成报告"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        if format == 'markdown':
            content = self._gen_markdown(metrics, backtest_result, layer_result)
            filename = f"backtest_report_{timestamp}.md"
        else:
            content = self._gen_html(metrics, backtest_result, layer_result)
            filename = f"backtest_report_{timestamp}.html"
        
        filepath = self.output_dir / filename
        filepath.write_text(content, encoding='utf-8')
        
        logger.info(f"报告生成: {filepath}")
        return filepath
    
    def _gen_markdown(
        self,
        metrics: Dict,
        result: Dict,
        layer: pd.DataFrame
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
            if isinstance(value, float):
                lines.append(f"| {key} | {value:.4f} |")
            else:
                lines.append(f"| {key} | {value} |")
        
        lines.extend([
            "",
            "## 二、收益统计",
            "",
            f"- 初始资金: {result.get('initial', 'N/A'):,.0f}",
            f"- 最终资金: {result.get('final', 'N/A'):,.0f}",
            f"- 总收益率: {result.get('total_return', 0)*100:.2f}%",
            f"- 交易次数: {result.get('trades', 0)}",
            "",
        ])
        
        if layer is not None and not layer.empty:
            lines.extend([
                "## 三、分层分析",
                "",
                layer.to_markdown(),
                "",
            ])
        
        lines.extend([
            "---",
            "*量化开发经理 (KkTTM7)*"
        ])
        
        return "\n".join(lines)
    
    def _gen_html(
        self,
        metrics: Dict,
        result: Dict,
        layer: pd.DataFrame
    ) -> str:
        # 简化HTML生成
        return f"<html><body><h1>回测报告</h1><pre>{metrics}</pre></body></html>"