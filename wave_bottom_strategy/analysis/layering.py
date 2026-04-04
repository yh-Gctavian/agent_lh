# -*- coding: utf-8 -*-
"""分层分析 - 按因子分值分组分析收益率"""

from typing import Dict, List, Optional
import pandas as pd
import numpy as np

from wave_bottom_strategy.utils.logger import get_logger

logger = get_logger('layering')


class LayeringAnalysis:
    """分层分析
    
    将股票按因子得分分成N层，分析各层的收益表现
    """
    
    def __init__(self, n_layers: int = 5):
        self.n_layers = n_layers
    
    def layer_by_score(
        self,
        scores: pd.DataFrame,
        returns: pd.Series = None
    ) -> pd.DataFrame:
        """按因子得分分层"""
        if scores.empty:
            return pd.DataFrame()
        
        df = scores.copy()
        
        if 'total_score' not in df.columns:
            logger.warning("得分数据缺少 total_score 列")
            return pd.DataFrame()
        
        df = df.sort_values('total_score', ascending=False)
        
        try:
            df['layer'] = pd.qcut(df['total_score'], self.n_layers, labels=False, duplicates='drop')
        except:
            n = len(df)
            df['layer'] = np.floor(np.arange(n) / (n / self.n_layers)).astype(int)
            df['layer'] = df['layer'].clip(0, self.n_layers - 1)
        
        if returns is not None:
            df['return'] = df['ts_code'].map(returns)
        
        results = []
        for layer_id in sorted(df['layer'].unique()):
            layer_data = df[df['layer'] == layer_id]
            
            result = {
                'layer': int(layer_id) + 1,
                'count': len(layer_data),
                'avg_score': layer_data['total_score'].mean(),
                'min_score': layer_data['total_score'].min(),
                'max_score': layer_data['total_score'].max()
            }
            
            if 'return' in layer_data.columns:
                layer_returns = layer_data['return'].dropna()
                if len(layer_returns) > 0:
                    result['avg_return'] = layer_returns.mean()
                    result['win_rate'] = (layer_returns > 0).mean()
            
            results.append(result)
        
        return pd.DataFrame(results)
    
    def find_best_layer(self, layer_df: pd.DataFrame) -> Dict:
        """找出表现最好的层"""
        if layer_df.empty or 'avg_return' not in layer_df.columns:
            return {}
        
        best_layer = layer_df.loc[layer_df['avg_return'].idxmax()]
        
        return {
            'best_layer': int(best_layer['layer']),
            'avg_return': best_layer['avg_return'],
            'win_rate': best_layer['win_rate'] if 'win_rate' in best_layer else 0
        }
    
    def generate_report(self, layer_df: pd.DataFrame) -> Dict:
        """生成分层分析报告"""
        if layer_df.empty:
            return {}
        
        return {
            'n_layers': len(layer_df),
            'total_stocks': layer_df['count'].sum(),
            'best_layer': self.find_best_layer(layer_df),
            'layer_summary': layer_df.to_dict('records')
        }


class ICAnalysis:
    """IC分析 - 因子有效性评估"""
    
    def calc_ic(self, factor_values: pd.Series, returns: pd.Series) -> float:
        """计算IC值"""
        df = pd.DataFrame({'factor': factor_values, 'return': returns})
        df = df.dropna()
        
        if len(df) < 10:
            return 0
        
        ic = df['factor'].corr(df['return'], method='spearman')
        return ic if not np.isnan(ic) else 0
    
    def calc_ic_series(self, factor_dict: Dict, returns: pd.Series) -> pd.DataFrame:
        """计算多因子IC"""
        results = []
        
        for factor_name, factor_values in factor_dict.items():
            ic = self.calc_ic(factor_values, returns)
            results.append({'factor': factor_name, 'ic': ic, 'ic_abs': abs(ic)})
        
        return pd.DataFrame(results)