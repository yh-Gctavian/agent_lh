# -*- coding: utf-8 -*-
"""Sensitivity analysis"""

from typing import Dict, List, Any
import pandas as pd
from itertools import product


class SensitivityAnalysis:
    """Parameter sensitivity analysis"""
    
    def __init__(self, param_ranges: Dict[str, List[Any]] = None):
        self.param_ranges = param_ranges or {}
    
    def generate_combinations(self) -> List[Dict]:
        """Generate parameter combinations"""
        if not self.param_ranges:
            return [{}]
        keys = list(self.param_ranges.keys())
        values = list(self.param_ranges.values())
        return [dict(zip(keys, combo)) for combo in product(*values)]
    
    def run_analysis(self, backtest_func, base_params: Dict = None) -> pd.DataFrame:
        """Run sensitivity analysis"""
        combinations = self.generate_combinations()
        base_params = base_params or {}
        results = []
        
        for params in combinations:
            full_params = {**base_params, **params}
            try:
                metrics = backtest_func(full_params)
                results.append({**params, **metrics})
            except Exception as e:
                results.append({**params, 'error': str(e)})
        
        return pd.DataFrame(results)
    
    def find_optimal(self, results: pd.DataFrame, metric: str = 'sharpe_ratio') -> Dict:
        """Find optimal parameters"""
        if metric not in results.columns:
            return {}
        valid = results[results[metric].notna()]
        if valid.empty:
            return {}
        return valid.loc[valid[metric].idxmax()].to_dict()