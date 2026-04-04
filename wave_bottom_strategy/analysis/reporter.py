# -*- coding: utf-8 -*-
"""报告生成器 - 生成回测分析报告"""

from typing import Dict, List, Optional
from pathlib import Path
from datetime import datetime
import pandas as pd
import json

from wave_bottom_strategy.utils.logger import get_logger

logger = get_logger('reporter')


class ReportGenerator:
    """报告生成器
    
    支持生成：
    - Markdown报告
    - HTML报告（带图表）
    - JSON数据报告
    """
    
    def __init__(self, output_dir: Path = None):
        """
        Args:
            output_dir: 报告输出目录
        """
        self.output_dir = output_dir or Path('data/results/reports')
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_markdown(
        self,
        metrics: Dict,
        trade_analysis: Dict = None,
        layer_analysis: Dict = None,
        sensitivity_analysis: Dict = None,
        chart_paths: Dict = None
    ) -> Path:
        """生成Markdown报告
        
        Args:
            metrics: 绩效指标
            trade_analysis: 交易分析
            layer_analysis: 分层分析
            sensitivity_analysis: 敏感性分析
            chart_paths: 图表路径
            
        Returns:
            报告文件路径
        """
        lines = [
            "# 波段抄底策略 - 回测分析报告",
            "",
            f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "---",
            "",
            "## 一、绩效指标",
            "",
            "### 收益指标",
            "",
            f"| 指标 | 数值 |",
            f"|------|------|",
            f"| 累计收益率 | {metrics.get('cumulative_return', 0)*100:.2f}% |",
            f"| 年化收益率 | {metrics.get('annualized_return', 0)*100:.2f}% |",
            f"| 年化波动率 | {metrics.get('volatility', 0)*100:.2f}% |",
            "",
            "### 风险指标",
            "",
            f"| 指标 | 数值 |",
            f"|------|------|",
            f"| 最大回撤 | {metrics.get('max_drawdown', 0)*100:.2f}% |",
            f"| 夏普比率 | {metrics.get('sharpe_ratio', 0):.2f} |",
            f"| 卡玛比率 | {metrics.get('calmar_ratio', 0):.2f} |",
            f"| 索提诺比率 | {metrics.get('sortino_ratio', 0):.2f} |",
            ""
        ]
        
        # 基准对比
        if 'benchmark' in metrics:
            lines.extend([
                "### 基准对比",
                "",
                f"| 指标 | 数值 |",
                f"|------|------|",
                f"| 基准收益率 | {metrics['benchmark'].get('benchmark_return', 0)*100:.2f}% |",
                f"| 超额收益率 | {metrics['benchmark'].get('excess_return', 0)*100:.2f}% |",
                ""
            ])
        
        # 交易统计
        if trade_analysis:
            lines.extend([
                "## 二、交易分析",
                "",
                f"| 指标 | 数值 |",
                f"|------|------|",
                f"| 总交易次数 | {trade_analysis.get('total_round_trips', 0)} |",
                f"| 盈利次数 | {trade_analysis.get('win_count', 0)} |",
                f"| 亏损次数 | {trade_analysis.get('loss_count', 0)} |",
                f"| 胜率 | {trade_analysis.get('win_rate', 0)*100:.2f}% |",
                f"| 平均盈利 | {trade_analysis.get('avg_win', 0):.2f} |",
                f"| 平均亏损 | {trade_analysis.get('avg_loss', 0):.2f} |",
                f"| 盈亏比 | {trade_analysis.get('profit_factor', 0):.2f} |",
                f"| 平均持仓天数 | {trade_analysis.get('avg_holding_days', 0):.1f} |",
                ""
            ])
        
        # 分层分析
        if layer_analysis:
            lines.extend([
                "## 三、分层分析",
                "",
                f"分层数: {layer_analysis.get('n_layers', 0)}",
                "",
                "### 各层表现",
                ""
            ])
            
            for layer in layer_analysis.get('layer_summary', []):
                lines.append(
                    f"- 第{layer['layer']}层: 平均收益 {layer.get('avg_return', 0)*100:.2f}%, "
                    f"胜率 {layer.get('win_rate', 0)*100:.1f}%"
                )
            
            best = layer_analysis.get('best_layer', {})
            if best:
                lines.extend([
                    "",
                    f"**最优层**: 第{best.get('best_layer', 0)}层",
                    ""
                ])
        
        # 敏感性分析
        if sensitivity_analysis:
            lines.extend([
                "## 四、参数敏感性分析",
                "",
                f"测试组合数: {sensitivity_analysis.get('total_combinations', 0)}",
                "",
                "### 最优参数",
                ""
            ])
            
            for params in sensitivity_analysis.get('best_params', [])[:3]:
                lines.append(f"- {params}")
            
            lines.extend([
                "",
                "### 参数重要性排序",
                ""
            ])
            
            for imp in sensitivity_analysis.get('param_importance', []):
                lines.append(
                    f"- {imp['param']}: 影响范围 {imp['impact_range']:.4f}"
                )
        
        # 图表链接
        if chart_paths:
            lines.extend([
                "",
                "## 五、可视化图表",
                ""
            ])
            
            for name, path in chart_paths.items():
                if path:
                    lines.append(f"- {name}: `{path}`")
        
        # 保存
        output_path = self.output_dir / f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
        
        logger.info(f"Markdown报告已生成: {output_path}")
        
        return output_path
    
    def generate_html(
        self,
        metrics: Dict,
        chart_paths: Dict = None,
        title: str = "波段抄底策略回测报告"
    ) -> Path:
        """生成HTML报告
        
        Args:
            metrics: 绩效指标
            chart_paths: 图表路径
            title: 报告标题
            
        Returns:
            报告文件路径
        """
        html_content = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>{title}</title>
    <style>
        body {{ font-family: 'Microsoft YaHei', sans-serif; margin: 20px; background: #f5f5f5; }}
        h1 {{ color: #2E86AB; }}
        h2 {{ color: #A23B72; margin-top: 20px; }}
        table {{ border-collapse: collapse; width: 100%; margin: 10px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background: #2E86AB; color: white; }}
        .metric {{ background: white; padding: 15px; margin: 10px; border-radius: 5px; }}
        .positive {{ color: green; }}
        .negative {{ color: red; }}
    </style>
</head>
<body>
    <h1>{title}</h1>
    <p>生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    
    <h2>绩效指标</h2>
    <div class="metric">
        <table>
            <tr><th>指标</th><th>数值</th></tr>
            <tr><td>累计收益率</td><td class="{('positive' if metrics.get('cumulative_return', 0) > 0 else 'negative')}">{metrics.get('cumulative_return', 0)*100:.2f}%</td></tr>
            <tr><td>年化收益率</td><td class="{('positive' if metrics.get('annualized_return', 0) > 0 else 'negative')}">{metrics.get('annualized_return', 0)*100:.2f}%</td></tr>
            <tr><td>夏普比率</td><td>{metrics.get('sharpe_ratio', 0):.2f}</td></tr>
            <tr><td>最大回撤</td><td class="negative">{metrics.get('max_drawdown', 0)*100:.2f}%</td></tr>
        </table>
    </div>
    
    <h2>图表分析</h2>
    <div class="metric">
"""
        
        if chart_paths:
            for name, path in chart_paths.items():
                if path and path.endswith('.png'):
                    html_content += f'<p><strong>{name}</strong></p><img src="{path}" width="80%"><br>\n'
        
        html_content += """
    </div>
</body>
</html>
"""
        
        output_path = self.output_dir / f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        logger.info(f"HTML报告已生成: {output_path}")
        
        return output_path
    
    def generate_json(self, data: Dict) -> Path:
        """生成JSON数据报告
        
        Args:
            data: 数据字典
            
        Returns:
            报告文件路径
        """
        output_path = self.output_dir / f"data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        return output_path
    
    def generate_full_report(
        self,
        metrics: Dict,
        trade_analysis: Dict = None,
        layer_analysis: Dict = None,
        sensitivity_analysis: Dict = None,
        chart_paths: Dict = None
    ) -> Dict[str, Path]:
        """生成完整报告
        
        Args:
            metrics: 绩效指标
            trade_analysis: 交易分析
            layer_analysis: 分层分析
            sensitivity_analysis: 敏感性分析
            chart_paths: 图表路径
            
        Returns:
            各格式报告路径
        """
        paths = {}
        
        # Markdown
        paths['markdown'] = self.generate_markdown(
            metrics, trade_analysis, layer_analysis, sensitivity_analysis, chart_paths
        )
        
        # HTML
        paths['html'] = self.generate_html(metrics, chart_paths)
        
        # JSON
        full_data = {
            'metrics': metrics,
            'trade_analysis': trade_analysis,
            'layer_analysis': layer_analysis,
            'sensitivity_analysis': sensitivity_analysis,
            'generated_at': datetime.now().isoformat()
        }
        paths['json'] = self.generate_json(full_data)
        
        logger.info(f"完整报告已生成: {len(paths)}个文件")
        
        return paths