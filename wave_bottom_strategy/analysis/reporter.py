# -*- coding: utf-8 -*-
"""Report generator"""

from typing import Dict
from pathlib import Path
from datetime import datetime


class ReportGenerator:
    """Report generator"""
    
    def __init__(self, output_dir: Path = None):
        self.output_dir = output_dir or Path('reports')
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def generate(self, metrics: Dict, result: Dict) -> Path:
        """Generate report"""
        lines = [
            "# Wave Bottom Strategy Backtest Report",
            "",
            "Generated: %s" % datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "",
            "## Performance Metrics",
            "",
            "- Win Rate: %.2f%%" % (metrics.get('win_rate', 0) * 100),
            "- Sharpe Ratio: %.2f" % metrics.get('sharpe_ratio', 0),
            "- Max Drawdown: %.2f%%" % (metrics.get('max_drawdown', 0) * 100),
            "",
            "Initial Capital: %.0f" % result.get('initial', 0),
            "Final Value: %.0f" % result.get('final', 0),
        ]
        
        output_path = self.output_dir / ("report_%s.md" % datetime.now().strftime('%Y%m%d_%H%M%S'))
        output_path.write_text("\n".join(lines), encoding='utf-8')
        return output_path