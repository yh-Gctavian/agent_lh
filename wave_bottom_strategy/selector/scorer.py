# -*- coding: utf-8 -*-
"""因子打分器 - 多因子加权合成"""

from typing import List, Dict
import pandas as pd

from factors.base import Factor
from factors.kdj import KDJFactor
from factors.ma import MAFactor
from factors.volume import VolumeFactor
from factors.rsi import RSIFactor
from factors.macd import MACDFactor
from factors.bollinger import BollingerFactor
from utils.logger import get_logger

logger = get_logger('factor_scorer')


class FactorScorer:
    """因子打分器
    
    计算6因子得分并加权合成总分
    """
    
    def __init__(self, factors: List[Factor] = None):
        """初始化
        
        Args:
            factors: 因子列表，默认使用全部6因子
        """
        if factors is None:
            # 默认使用全部因子
            self.factors = [
                KDJFactor(),      # 45%
                VolumeFactor(),   # 15%
                MAFactor(),       # 15%
                RSIFactor(),      # 10%
                MACDFactor(),     # 10%
                BollingerFactor(), # 5%
            ]
        else:
            self.factors = factors
        
        logger.info(f"因子打分器初始化: {len(self.factors)}个因子")
    
    def calculate_all_factors(self, data: pd.DataFrame) -> Dict[str, pd.DataFrame]:
        """计算所有因子
        
        Args:
            data: 日K线数据
            
        Returns:
            {因子名: 因子计算结果}
        """
        results = {}
        
        for factor in self.factors:
            try:
                factor_data = factor.calculate(data)
                results[factor.name] = factor_data
                logger.debug(f"{factor.name} 计算完成")
            except Exception as e:
                logger.error(f"{factor.name} 计算失败: {e}")
        
        return results
    
    def get_factor_scores(self, factor_results: Dict[str, pd.DataFrame]) -> Dict[str, pd.Series]:
        """获取各因子得分
        
        Args:
            factor_results: 因子计算结果
            
        Returns:
            {因子名: 得分序列}
        """
        scores = {}
        
        for factor in self.factors:
            factor_name = factor.name
            if factor_name in factor_results:
                factor_data = factor_results[factor_name]
                
                # 调用因子的get_score方法
                if hasattr(factor, 'get_score'):
                    score = factor.get_score(factor_data)
                    scores[factor_name] = score
                else:
                    # 默认得分
                    scores[factor_name] = pd.Series(50.0, index=factor_data.index)
        
        return scores
    
    def calculate_total_score(
        self,
        factor_scores: Dict[str, pd.Series],
        weights: Dict[str, float] = None
    ) -> pd.Series:
        """计算加权总分
        
        Args:
            factor_scores: 各因子得分
            weights: 自定义权重，默认使用因子自带权重
            
        Returns:
            加权总分序列
        """
        if weights is None:
            # 使用因子自带权重
            weights = {f.name: f.weight for f in self.factors}
        
        total_score = pd.Series(0.0, index=factor_scores[list(factor_scores.keys())[0]].index)
        total_weight = 0.0
        
        for factor_name, score in factor_scores.items():
            weight = weights.get(factor_name, 0)
            total_score += score * weight
            total_weight += weight
        
        # 归一化（确保总分在0-100）
        if total_weight > 0:
            total_score = total_score / total_weight
        
        logger.info(f"总分计算完成, 权重总和: {total_weight}")
        
        return total_score
    
    def score_stock(self, data: pd.DataFrame) -> pd.DataFrame:
        """对单只股票完整评分
        
        Args:
            data: 日K线数据
            
        Returns:
            包含各因子得分和总分的DataFrame
        """
        # 计算所有因子
        factor_results = self.calculate_all_factors(data)
        
        # 获取各因子得分
        factor_scores = self.get_factor_scores(factor_results)
        
        # 计算总分
        total_score = self.calculate_total_score(factor_scores)
        
        # 组装结果
        result = pd.DataFrame()
        result['trade_date'] = data['trade_date'] if 'trade_date' in data.columns else data.index
        
        # 添加各因子得分
        for factor_name, score in factor_scores.items():
            result[f'{factor_name}_score'] = score
        
        result['total_score'] = total_score
        
        return result
    
    def get_top_stocks(
        self,
        scores_df: pd.DataFrame,
        top_n: int = 10,
        min_score: float = 60.0
    ) -> pd.DataFrame:
        """获取得分最高的股票
        
        Args:
            scores_df: 评分结果
            top_n: 返回数量
            min_score: 最低得分阈值
            
        Returns:
            Top N股票
        """
        # 过滤最低得分
        qualified = scores_df[scores_df['total_score'] >= min_score]
        
        # 按总分排序
        top = qualified.nlargest(top_n, 'total_score')
        
        return top