# -*- coding: utf-8 -*-
"""Report generator"""

from typing import Dict, Optional
from pathlib import Path
import pandas as pd
from datetime import datetime


class ReportGenerator:
    """Generate backtest analysis reports"""
    
    def __init__(self, output_dir: Path = None):
        self.output_dir = output_dir or Path('reports')
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def generate(self, metrics: Dict, backtest_result: Dict, format: str = 'markdown') -> Path:
        """Generate report"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        content = self._generate_markdown(metrics, backtest_result)
        
        filename = f"backtest_report_{timestamp}.md"
        output_path = self.output_dir / filename
        output_path.write_text(content, encoding='utf-8')
        return output_path
    
    def _generate_markdown(self, metrics: Dict, backtest_result: Dict) -> str:
        """Generate markdown report"""
        lines = [
            "# Wave Bottom Strategy Backtest Report",
            "",
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## Performance Metrics",
            "",
            "| Metric | Value |",
            "|--------|-------|",
        ]
        for key, value in metrics.items():
            if isinstance(value, float):
                lines.append(f"| {key} | {value:.4f} |")
            else:
                lines.append(f"| {key} | {value} |")
        
        return "\n".join(lines)