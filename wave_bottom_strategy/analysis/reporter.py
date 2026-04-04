# -*- coding: utf-8 -*-
"""报告生成器"""

from typing import Dict
from pathlib import Path
from datetime import datetime


class ReportGenerator:
    """报告生成器"""
    
    def __init__(self, output_dir: Path = None):
        self.output_dir = output_dir or Path('reports')
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def generate(self, metrics: Dict, result: Dict) -> Path:
        """生成报告"""
        lines = [
            "# 波段抄底策略回测报告",
            "",
            f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## 绩效指标",
            "",
            f"- 胜率: {metrics.get('win_rate', 0):.2%}",
            f"- 夏普比率: {metrics.get('sharpe_ratio', 0):.2f}",
            f"- 最大回撤: {metrics.get('max_drawdown', 0):.2%}",
            "",
            f"初始资金: {result.get('initial', 0):,.0f}",
            f"最终净值: {result.get('final', 0):,.0f}",
        ]
        
        output_path = self.output_dir / f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        output_path.write_text("\n".join(lines), encoding='utf-8')
        return output_path