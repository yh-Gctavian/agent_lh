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
    
    生成回测分析报告（Markdown格式）
    """
    
    def __init__(self, output_dir: Path = None):
        self.output_dir = output_dir or Path('reports')
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def generate(
        self,
        metrics: Dict,
        daily_df: pd.DataFrame = None,
        layer_result: Optional[pd.DataFrame] = None,
        sensitivity_result: Optional[pd.DataFrame] = None,
        title: str = "波段抄底策略回测报告"
    ) -> Path:
        """生成报告
        
        Args:
            metrics: 绩效指标
            daily_df: 日净值数据
            layer_result: 分层分析结果
            sensitivity_result: 敏感性分析结果
            title: 报告标题
            
        Returns:
            报告文件路径
        """
        content = self._build_content(
            metrics, daily_df, layer_result, sensitivity_result, title
        )
        
        filename = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        filepath = self.output_dir / filename
        
        filepath.write_text(content, encoding='utf-8')
        logger.info(f"报告已生成: {filepath}")
        
        return filepath
    
    def _build_content(
        self,
        metrics: Dict,
        daily_df: pd.DataFrame,
        layer_result: pd.DataFrame,
        sensitivity_result: pd.DataFrame,
        title: str
    ) -> str:
        """构建报告内容"""
        lines = [
            f"# {title}",
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
        
        # 指标表格
        metric_names = {
            'win_rate': '胜率(%)',
            'profit_loss_ratio': '盈亏比',
            'sharpe_ratio': '夏普比率',
            'max_drawdown': '最大回撤(%)',
            'annual_return': '年化收益(%)',
            'volatility': '年化波动(%)',
            'calmar_ratio': '卡玛比率'
        }
        
        for key, value in metrics.items():
            name = metric_names.get(key, key)
            lines.append(f"| {name} | {value} |")
        
        # 净值曲线
        if daily_df is not None and not daily_df.empty:
            lines.extend([
                "",
                "---",
                "",
                "## 二、净值曲线",
                "",
                "| 日期 | 净值 | 收益率 |",
                "|------|------|--------|"
            ])
            
            for _, row in daily_df.tail(20).iterrows():
                date_str = str(row.get('date', row.get('trade_date', '')))
                value = row.get('value', row.get('total_value', 0))
                ret = row.get('return', 0)
                lines.append(f"| {date_str} | {value:.2f} | {ret*100:.2f}% |")
        
        # 分层分析
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
        
        # 参数敏感性
        if sensitivity_result is not None and not sensitivity_result.empty:
            lines.extend([
                "",
                "---",
                "",
                "## 四、参数敏感性分析",
                "",
                "### Top 5 参数组合",
                "",
                sensitivity_result.head(5).to_markdown(index=False),
                ""
            ])
        
        # 总结
        lines.extend([
            "",
            "---",
            "",
            "## 五、结论",
            "",
            f"- 年化收益：{metrics.get('annual_return', 'N/A')}%",
            f"- 最大回撤：{metrics.get('max_drawdown', 'N/A')}%",
            f"- 夏普比率：{metrics.get('sharpe_ratio', 'N/A')}",
            "",
            "---",
            "",
            "*报告由量化开发经理 (KkTTM7) 生成*"
        ])
        
        return "\n".join(lines)
    
    def generate_simple(self, backtest_result: Dict) -> Path:
        """生成简单报告
        
        Args:
            backtest_result: 回测结果
            
        Returns:
            报告路径
        """
        metrics = {
            'annual_return': backtest_result.get('total_return', 0) * 100,
            'trade_count': backtest_result.get('trades', 0)
        }
        
        daily_df = backtest_result.get('daily_df')
        
        return self.generate(
            metrics=metrics,
            daily_df=daily_df,
            title="波段抄底策略回测报告"
        )