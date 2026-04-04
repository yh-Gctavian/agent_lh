# -*- coding: utf-8 -*-
"""报告生成器"""

from typing import Dict, Optional, List
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
        backtest_result: Dict = None,
        sensitivity_result: pd.DataFrame = None,
        walk_forward_result: Dict = None,
        format: str = 'markdown'
    ) -> Path:
        """生成报告"""
        if format == 'markdown':
            content = self._gen_markdown(metrics, backtest_result, sensitivity_result, walk_forward_result)
            filename = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        else:
            content = self._gen_html(metrics, backtest_result)
            filename = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        
        filepath = self.output_dir / filename
        filepath.write_text(content, encoding='utf-8')
        
        logger.info(f"报告生成: {filepath}")
        return filepath
    
    def _gen_markdown(self, metrics, backtest, sensitivity, walk_forward) -> str:
        lines = [
            "# 波段抄底策略分析报告",
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
        
        if walk_forward:
            lines.extend([
                "",
                "## 二、Walk-Forward验证",
                "",
                f"- 训练期: {walk_forward.get('train_period', 'N/A')}",
                f"- 测试期: {walk_forward.get('test_period', 'N/A')}",
                f"- 过拟合度: {walk_forward.get('overfitting_score', 0):.2%}",
                "",
                "### 最优参数",
                "",
                "```json",
                str(walk_forward.get('optimal_params', {})),
                "```",
            ])
        
        if sensitivity is not None and not sensitivity.empty:
            lines.extend([
                "",
                "## 三、参数敏感性分析",
                "",
                sensitivity.head(10).to_markdown(),
            ])
        
        lines.extend([
            "",
            "---",
            "*量化开发经理 (KkTTM7)*"
        ])
        
        return "\n".join(lines)
    
    def _gen_html(self, metrics, backtest) -> str:
        return f"<html><body><h1>报告</h1><pre>{metrics}</pre></body></html>"