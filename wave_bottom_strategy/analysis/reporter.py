# -*- coding: utf-8 -*-
"""报告生成器"""

from typing import Dict, Optional
from pathlib import Path
import pandas as pd
from datetime import datetime

from utils.logger import get_logger

logger = get_logger('report_generator')


class ReportGenerator:
    """报告生成器
    
    生成回测分析报告（Markdown/HTML）
    """
    
    def __init__(self, output_dir: Path = None):
        self.output_dir = output_dir or Path('reports')
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def generate(
        self,
        metrics: Dict,
        backtest_result: Dict,
        layer_result: Optional[pd.DataFrame] = None,
        sensitivity_result: Optional[pd.DataFrame] = None,
        format: str = 'markdown'
    ) -> Path:
        """生成报告"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        if format == 'markdown':
            content = self._generate_markdown(metrics, backtest_result, layer_result, sensitivity_result)
            filename = f"backtest_report_{timestamp}.md"
        else:
            content = self._generate_html(metrics, backtest_result, layer_result, sensitivity_result)
            filename = f"backtest_report_{timestamp}.html"
        
        filepath = self.output_dir / filename
        filepath.write_text(content, encoding='utf-8')
        
        logger.info(f"报告生成: {filepath}")
        return filepath
    
    def _generate_markdown(
        self,
        metrics: Dict,
        backtest_result: Dict,
        layer_result: Optional[pd.DataFrame],
        sensitivity_result: Optional[pd.DataFrame]
    ) -> str:
        """生成Markdown报告"""
        lines = [
            "# 波段抄底策略回测报告",
            "",
            f"**生成时间：** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "---",
            "",
            "## 一、核心绩效指标",
            "",
            "| 指标 | 值 |",
            "|------|------|",
        ]
        
        # 指标映射
        metric_names = {
            'total_return': '总收益率',
            'annual_return': '年化收益率',
            'volatility': '年化波动率',
            'sharpe_ratio': '夏普比率',
            'max_drawdown': '最大回撤',
            'calmar_ratio': '卡玛比率',
            'win_rate': '胜率',
            'profit_loss_ratio': '盈亏比'
        }
        
        for key, name in metric_names.items():
            value = metrics.get(key, 0)
            if isinstance(value, float):
                lines.append(f"| {name} | {value:.4f} |")
            else:
                lines.append(f"| {name} | {value} |")
        
        lines.extend(["", "---", "", "## 二、回测概况", ""])
        
        if 'initial' in backtest_result:
            lines.append(f"- 初始资金: {backtest_result['initial']:,.0f}")
        if 'final' in backtest_result:
            lines.append(f"- 最终资金: {backtest_result['final']:,.0f}")
        if 'trades' in backtest_result:
            lines.append(f"- 交易次数: {backtest_result['trades']}")
        
        if layer_result is not None and not layer_result.empty:
            lines.extend([
                "",
                "---",
                "",
                "## 三、分层分析",
                "",
                layer_result.to_markdown(index=False),
                ""
            ])
        
        if sensitivity_result is not None and not sensitivity_result.empty:
            lines.extend([
                "",
                "---",
                "",
                "## 四、参数敏感性分析",
                "",
                sensitivity_result.head(10).to_markdown(index=False),
                ""
            ])
        
        lines.extend([
            "",
            "---",
            "",
            "*报告由波段抄底策略系统自动生成*"
        ])
        
        return "\n".join(lines)
    
    def _generate_html(
        self,
        metrics: Dict,
        backtest_result: Dict,
        layer_result: Optional[pd.DataFrame],
        sensitivity_result: Optional[pd.DataFrame]
    ) -> str:
        """生成HTML报告"""
        # 简化版HTML
        md_content = self._generate_markdown(metrics, backtest_result, layer_result, sensitivity_result)
        
        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>波段抄底策略回测报告</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        table {{ border-collapse: collapse; width: 100%; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
        h1 {{ color: #333; }}
        h2 {{ color: #666; }}
    </style>
</head>
<body>
    <pre>{md_content}</pre>
</body>
</html>"""
        
        return html
    
    def generate_summary(
        self,
        all_results: List[Dict]
    ) -> pd.DataFrame:
        """生成多回测汇总"""
        return pd.DataFrame(all_results)