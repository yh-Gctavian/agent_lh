# -*- coding: utf-8 -*-
"""报告生成器"""

from typing import Dict, Optional
from pathlib import Path
from datetime import datetime
import pandas as pd

from utils.logger import get_logger

logger = get_logger('reporter')


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
        daily_values: pd.DataFrame = None,
        trade_records: pd.DataFrame = None,
        sensitivity_result: pd.DataFrame = None,
        walk_forward_result: pd.DataFrame = None,
        format: str = 'markdown'
    ) -> Path:
        """生成报告
        
        Args:
            metrics: 绩效指标
            daily_values: 每日净值
            trade_records: 交易记录
            sensitivity_result: 敏感性分析结果
            walk_forward_result: Walk-Forward结果
            format: 输出格式
            
        Returns:
            报告文件路径
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        if format == 'markdown':
            content = self._generate_markdown(
                metrics, daily_values, trade_records,
                sensitivity_result, walk_forward_result
            )
            filename = f"backtest_report_{timestamp}.md"
        else:
            content = self._generate_html(
                metrics, daily_values, trade_records,
                sensitivity_result, walk_forward_result
            )
            filename = f"backtest_report_{timestamp}.html"
        
        filepath = self.output_dir / filename
        filepath.write_text(content, encoding='utf-8')
        
        logger.info(f"报告生成: {filepath}")
        
        return filepath
    
    def _generate_markdown(
        self,
        metrics: Dict,
        daily_values: pd.DataFrame,
        trade_records: pd.DataFrame,
        sensitivity_result: pd.DataFrame,
        walk_forward_result: pd.DataFrame
    ) -> str:
        """生成Markdown报告"""
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
        
        lines.extend([
            "",
            "---",
            "",
            "## 二、收益曲线",
            "",
            "（图表待生成）",
            "",
        ])
        
        if daily_values is not None and not daily_values.empty:
            lines.extend([
                "### 每日净值统计",
                "",
                f"- 期初净值：{daily_values['total_value'].iloc[0]:.2f}",
                f"- 期末净值：{daily_values['total_value'].iloc[-1]:.2f}",
                f"- 最高净值：{daily_values['total_value'].max():.2f}",
                f"- 最低净值：{daily_values['total_value'].min():.2f}",
                "",
            ])
        
        if trade_records is not None and not trade_records.empty:
            lines.extend([
                "---",
                "",
                "## 三、交易记录",
                "",
                f"总交易次数：{len(trade_records)}",
                "",
            ])
        
        if sensitivity_result is not None and not sensitivity_result.empty:
            lines.extend([
                "---",
                "",
                "## 四、参数敏感性分析",
                "",
                sensitivity_result.to_markdown(),
                "",
            ])
        
        if walk_forward_result is not None and not walk_forward_result.empty:
            lines.extend([
                "---",
                "",
                "## 五、Walk-Forward验证",
                "",
                walk_forward_result.to_markdown(),
                "",
            ])
        
        lines.extend([
            "---",
            "",
            "*报告由量化开发经理 (KkTTM7) 生成*",
        ])
        
        return "\n".join(lines)
    
    def _generate_html(
        self,
        metrics: Dict,
        daily_values: pd.DataFrame,
        trade_records: pd.DataFrame,
        sensitivity_result: pd.DataFrame,
        walk_forward_result: pd.DataFrame
    ) -> str:
        """生成HTML报告"""
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>波段抄底策略回测报告</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        h1 {{ color: #333; }}
        h2 {{ color: #666; border-bottom: 1px solid #ccc; }}
        table {{ border-collapse: collapse; width: 100%; margin: 10px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #4CAF50; color: white; }}
        tr:nth-child(even) {{ background-color: #f2f2f2; }}
    </style>
</head>
<body>
    <h1>波段抄底策略回测报告</h1>
    <p>生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    
    <h2>一、绩效指标</h2>
    <table>
        <tr><th>指标</th><th>值</th></tr>
"""
        
        for key, value in metrics.items():
            if isinstance(value, float):
                html += f"        <tr><td>{key}</td><td>{value:.4f}</td></tr>\n"
            else:
                html += f"        <tr><td>{key}</td><td>{value}</td></tr>\n"
        
        html += """
    </table>
    
    <h2>二、收益曲线</h2>
    <p>（图表待生成）</p>
    
    <hr>
    <p><i>报告由量化开发经理 (KkTTM7) 生成</i></p>
</body>
</html>
"""
        
        return html
    
    def generate_summary(self, result: Dict) -> str:
        """生成简要摘要
        
        Args:
            result: 回测结果
            
        Returns:
            摘要文本
        """
        summary = f"""
回测结果摘要：
- 总收益率: {result.get('total_return', 0):.2%}
- 年化收益率: {result.get('annual_return', 0):.2%}
- 最大回撤: {result.get('max_drawdown', 0):.2%}
- 夏普比率: {result.get('sharpe', 0):.4f}
- 交易次数: {result.get('trade_count', 0)}
"""
        return summary