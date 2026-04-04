# -*- coding: utf-8 -*-
"""回测可视化模块 - 收益曲线、持仓分析、绩效图表"""

from typing import Dict, Optional, List
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime

from wave_bottom_strategy.utils.logger import get_logger

logger = get_logger('visualizer')


class BacktestVisualizer:
    """回测结果可视化器
    
    支持生成多种图表：
    - 收益曲线对比（策略 vs 基准）
    - 持仓分布饼图
    - 盈亏分布柱状图
    - 最大回撤图
    - 月度收益热力图
    """
    
    def __init__(self, output_dir: Path = None):
        """初始化
        
        Args:
            output_dir: 图表输出目录
        """
        self.output_dir = output_dir or Path('data/results/charts')
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def plot_return_curve(
        self,
        daily_values: pd.DataFrame,
        benchmark_values: pd.DataFrame = None,
        title: str = "策略收益曲线",
        save_path: str = None
    ) -> str:
        """绘制收益曲线
        
        Args:
            daily_values: 每日资产数据
            benchmark_values: 基准数据
            title: 图表标题
            save_path: 保存路径
            
        Returns:
            图表文件路径
        """
        try:
            import matplotlib.pyplot as plt
            import matplotlib.dates as mdates
            
            # 设置中文字体
            plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
            plt.rcParams['axes.unicode_minus'] = False
            
            fig, ax = plt.subplots(figsize=(12, 6))
            
            # 计算累计收益
            if 'total_value' in daily_values.columns:
                initial_value = daily_values['total_value'].iloc[0]
                cumulative_return = (daily_values['total_value'] / initial_value - 1) * 100
                
                ax.plot(daily_values['date'], cumulative_return, 
                       label='策略收益', linewidth=2, color='#2E86AB')
            
            # 基准对比
            if benchmark_values is not None and not benchmark_values.empty:
                if 'total_value' in benchmark_values.columns:
                    bench_initial = benchmark_values['total_value'].iloc[0]
                    bench_return = (benchmark_values['total_value'] / bench_initial - 1) * 100
                    
                    ax.plot(benchmark_values['date'], bench_return,
                           label='基准收益', linewidth=2, color='#A23B72', linestyle='--')
            
            ax.set_title(title, fontsize=14, fontweight='bold')
            ax.set_xlabel('日期', fontsize=12)
            ax.set_ylabel('累计收益率 (%)', fontsize=12)
            ax.legend(loc='upper left', fontsize=10)
            ax.grid(True, alpha=0.3)
            
            # 格式化日期轴
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
            ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
            plt.xticks(rotation=45)
            
            # 添加关键指标标注
            if 'total_value' in daily_values.columns:
                final_return = cumulative_return.iloc[-1]
                ax.annotate(f'{final_return:.2f}%', 
                           xy=(daily_values['date'].iloc[-1], final_return),
                           fontsize=10, color='#2E86AB')
            
            plt.tight_layout()
            
            # 保存图表
            if save_path is None:
                save_path = self.output_dir / f'return_curve_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png'
            else:
                save_path = Path(save_path)
            
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
            plt.close()
            
            logger.info(f"收益曲线已保存: {save_path}")
            return str(save_path)
            
        except ImportError:
            logger.warning("matplotlib未安装，跳过图表生成")
            return ""
        except Exception as e:
            logger.error(f"绘制收益曲线失败: {e}")
            return ""
    
    def plot_drawdown(
        self,
        daily_values: pd.DataFrame,
        title: str = "最大回撤分析",
        save_path: str = None
    ) -> str:
        """绘制回撤曲线
        
        Args:
            daily_values: 每日资产数据
            title: 图表标题
            save_path: 保存路径
            
        Returns:
            图表文件路径
        """
        try:
            import matplotlib.pyplot as plt
            
            plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei']
            plt.rcParams['axes.unicode_minus'] = False
            
            fig, ax = plt.subplots(figsize=(12, 4))
            
            if 'total_value' in daily_values.columns:
                values = daily_values['total_value']
                cummax = values.cummax()
                drawdown = (values - cummax) / cummax * 100
                
                ax.fill_between(daily_values['date'], 0, drawdown,
                               alpha=0.3, color='#E74C3C')
                ax.plot(daily_values['date'], drawdown,
                       color='#E74C3C', linewidth=1.5)
                
                # 标注最大回撤点
                max_dd_idx = drawdown.idxmin()
                max_dd = drawdown.iloc[max_dd_idx]
                ax.annotate(f'最大回撤: {abs(max_dd):.2f}%',
                           xy=(daily_values['date'].iloc[max_dd_idx], max_dd),
                           fontsize=10, color='#E74C3C')
            
            ax.set_title(title, fontsize=14)
            ax.set_xlabel('日期', fontsize=12)
            ax.set_ylabel('回撤 (%)', fontsize=12)
            ax.grid(True, alpha=0.3)
            
            plt.tight_layout()
            
            if save_path is None:
                save_path = self.output_dir / f'drawdown_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png'
            
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
            plt.close()
            
            return str(save_path)
            
        except Exception as e:
            logger.error(f"绘制回撤曲线失败: {e}")
            return ""
    
    def plot_position_distribution(
        self,
        trade_records: pd.DataFrame,
        title: str = "持仓分布",
        save_path: str = None
    ) -> str:
        """绘制持仓分布饼图
        
        Args:
            trade_records: 交易记录
            title: 图表标题
            save_path: 保存路径
            
        Returns:
            图表文件路径
        """
        try:
            import matplotlib.pyplot as plt
            
            plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei']
            
            if trade_records.empty or 'ts_code' not in trade_records.columns:
                return ""
            
            # 统计各股票交易次数
            buy_records = trade_records[trade_records['direction'] == 'buy']
            stock_counts = buy_records['ts_code'].value_counts().head(10)
            
            fig, ax = plt.subplots(figsize=(8, 8))
            
            colors = plt.cm.Set3(np.linspace(0, 1, len(stock_counts)))
            
            wedges, texts, autotexts = ax.pie(
                stock_counts.values,
                labels=stock_counts.index,
                autopct='%1.1f%%',
                colors=colors,
                startangle=90
            )
            
            ax.set_title(title, fontsize=14)
            
            plt.tight_layout()
            
            if save_path is None:
                save_path = self.output_dir / f'position_dist_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png'
            
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
            plt.close()
            
            return str(save_path)
            
        except Exception as e:
            logger.error(f"绘制持仓分布失败: {e}")
            return ""
    
    def plot_monthly_returns(
        self,
        daily_values: pd.DataFrame,
        title: str = "月度收益热力图",
        save_path: str = None
    ) -> str:
        """绘制月度收益热力图
        
        Args:
            daily_values: 每日资产数据
            title: 图表标题
            save_path: 保存路径
            
        Returns:
            图表文件路径
        """
        try:
            import matplotlib.pyplot as plt
            import seaborn as sns
            
            plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei']
            
            if daily_values.empty or 'date' not in daily_values.columns:
                return ""
            
            # 计算月度收益
            df = daily_values.copy()
            df['month'] = pd.to_datetime(df['date']).dt.month
            df['year'] = pd.to_datetime(df['date']).dt.year
            
            monthly_returns = df.groupby(['year', 'month'])['total_value'].apply(
                lambda x: (x.iloc[-1] / x.iloc[0] - 1) * 100 if len(x) > 1 else 0
            ).reset_index()
            
            # 构建热力图数据
            pivot_table = monthly_returns.pivot(index='year', columns='month', values=0)
            
            fig, ax = plt.subplots(figsize=(12, 6))
            
            sns.heatmap(pivot_table, annot=True, fmt='.2f', cmap='RdYlGn',
                       center=0, ax=ax, cbar_kws={'label': '收益率 (%)'})
            
            ax.set_title(title, fontsize=14)
            ax.set_xlabel('月份', fontsize=12)
            ax.set_ylabel('年份', fontsize=12)
            
            plt.tight_layout()
            
            if save_path is None:
                save_path = self.output_dir / f'monthly_returns_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png'
            
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
            plt.close()
            
            return str(save_path)
            
        except ImportError:
            logger.warning("seaborn未安装，跳过热力图生成")
            return ""
        except Exception as e:
            logger.error(f"绘制月度收益热力图失败: {e}")
            return ""
    
    def generate_full_report(
        self,
        daily_values: pd.DataFrame,
        trade_records: pd.DataFrame = None,
        benchmark_values: pd.DataFrame = None,
        metrics: Dict = None
    ) -> Dict[str, str]:
        """生成完整可视化报告
        
        Args:
            daily_values: 每日资产数据
            trade_records: 交易记录
            benchmark_values: 基准数据
            metrics: 绩效指标
            
        Returns:
            各图表文件路径字典
        """
        results = {}
        
        # 1. 收益曲线
        results['return_curve'] = self.plot_return_curve(
            daily_values, benchmark_values, "策略收益曲线对比"
        )
        
        # 2. 回撤分析
        results['drawdown'] = self.plot_drawdown(daily_values)
        
        # 3. 持仓分布
        if trade_records is not None:
            results['position_dist'] = self.plot_position_distribution(trade_records)
        
        # 4. 月度收益
        results['monthly_returns'] = self.plot_monthly_returns(daily_values)
        
        # 生成汇总报告
        report_path = self._generate_summary_report(results, metrics)
        results['summary_report'] = report_path
        
        logger.info(f"可视化报告生成完成: {len(results)}个图表")
        
        return results
    
    def _generate_summary_report(
        self,
        chart_paths: Dict[str, str],
        metrics: Dict = None
    ) -> str:
        """生成汇总报告（Markdown格式）
        
        Args:
            chart_paths: 图表路径
            metrics: 绩效指标
            
        Returns:
            报告文件路径
        """
        report_lines = [
            "# 回测可视化报告",
            "",
            f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## 图表列表",
            "",
        ]
        
        for name, path in chart_paths.items():
            if path:
                report_lines.append(f"- {name}: `{path}`")
        
        if metrics:
            report_lines.extend([
                "",
                "## 关键指标",
                "",
            ])
            for key, value in metrics.items():
                if isinstance(value, (int, float)):
                    report_lines.append(f"- {key}: {value:.4f}")
        
        report_content = "\n".join(report_lines)
        
        report_path = self.output_dir / f'visualization_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.md'
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        return str(report_path)


class PlotlyVisualizer:
    """交互式可视化器（Plotly实现）
    
    适合生成HTML交互图表
    """
    
    def __init__(self, output_dir: Path = None):
        self.output_dir = output_dir or Path('data/results/charts')
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def plot_interactive_return(
        self,
        daily_values: pd.DataFrame,
        benchmark_values: pd.DataFrame = None,
        save_path: str = None
    ) -> str:
        """生成交互式收益曲线
        
        Args:
            daily_values: 每日资产数据
            benchmark_values: 基准数据
            save_path: 保存路径
            
        Returns:
            HTML文件路径
        """
        try:
            import plotly.graph_objects as go
            from plotly.subplots import make_subplots
            
            fig = make_subplots(rows=2, cols=1, 
                               shared_xaxes=True,
                               vertical_spacing=0.03,
                               row_heights=[0.7, 0.3])
            
            # 收益曲线
            if 'total_value' in daily_values.columns:
                initial = daily_values['total_value'].iloc[0]
                returns = (daily_values['total_value'] / initial - 1) * 100
                
                fig.add_trace(
                    go.Scatter(x=daily_values['date'], y=returns,
                              name='策略收益', line=dict(color='#2E86AB', width=2)),
                    row=1, col=1
                )
            
            # 基准
            if benchmark_values is not None and not benchmark_values.empty:
                if 'total_value' in benchmark_values.columns:
                    bench_initial = benchmark_values['total_value'].iloc[0]
                    bench_returns = (benchmark_values['total_value'] / bench_initial - 1) * 100
                    
                    fig.add_trace(
                        go.Scatter(x=benchmark_values['date'], y=bench_returns,
                                  name='基准收益', line=dict(color='#A23B72', width=2, dash='dash')),
                        row=1, col=1
                    )
            
            # 回撤
            if 'total_value' in daily_values.columns:
                values = daily_values['total_value']
                cummax = values.cummax()
                drawdown = (values - cummax) / cummax * 100
                
                fig.add_trace(
                    go.Scatter(x=daily_values['date'], y=drawdown,
                              name='回撤', fill='tozeroy',
                              line=dict(color='#E74C3C', width=1)),
                    row=2, col=1
                )
            
            fig.update_layout(
                title='策略收益与回撤分析',
                xaxis_title='日期',
                yaxis_title='收益率 (%)',
                template='plotly_dark',
                hovermode='x unified'
            )
            
            if save_path is None:
                save_path = self.output_dir / f'interactive_return_{datetime.now().strftime("%Y%m%d_%H%M%S")}.html'
            
            fig.write_html(str(save_path))
            
            return str(save_path)
            
        except ImportError:
            logger.warning("plotly未安装，跳过交互图表生成")
            return ""
        except Exception as e:
            logger.error(f"生成交互图表失败: {e}")
            return ""