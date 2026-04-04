# -*- coding: utf-8 -*-
"""Layering analysis"""

import pandas as pd


class LayeringAnalysis:
    """Layer stocks by factor score and analyze returns"""
    
    def __init__(self, n_layers: int = 5):
        self.n_layers = n_layers
    
    def layer_by_score(self, scores: pd.Series, returns: pd.Series) -> pd.DataFrame:
        """Layer by factor score"""
        df = pd.DataFrame({'score': scores, 'return': returns})
        df = df.dropna()
        if len(df) == 0:
            return pd.DataFrame()
        
        df['layer'] = pd.qcut(df['score'], self.n_layers, labels=False, duplicates='drop')
        
        results = []
        for layer_id in df['layer'].unique():
            layer_data = df[df['layer'] == layer_id]
            results.append({
                'layer': layer_id + 1,
                'count': len(layer_data),
                'mean_return': layer_data['return'].mean(),
                'win_rate': (layer_data['return'] > 0).mean(),
            })
        
        return pd.DataFrame(results)