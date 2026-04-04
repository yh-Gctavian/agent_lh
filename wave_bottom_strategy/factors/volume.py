# -*- coding: utf-8 -*-
"""成交量因子 - 权重15%"""

from typing import Dict, Any
import pandas as pd
import numpy as np

from .base import Factor
from utils.logger import get_logger

logger = get_logger('volume_factor')


class VolumeFactor(Factor):
    """成交量因子
    
    参数:
        ma_period: 均量周期，默认5
    
    抄底信号:
        - 放量下跌: 可能是恐慌抛售，关注底部
        - 缩量下跌: 卖盘枯竭，接近底部
        - 放量上涨: 确认底部反弹
    """
    
    def __init__(self, params: Dict[str, Any] = None):
        super().__init__(params)
        self.ma_period = self.params.get('ma_period', 5)
    
    def calculate(self, data: pd.DataFrame) -> pd.DataFrame:
        """计算成交量指标
        
        Args:
            data: 日K线数据
            
        Returns:
            包含成交量指标的DataFrame
        """
        volume = data['volume'].values
        close = data['close'].values
        
        result = pd.DataFrame()
        result['trade_date'] = data['trade_date'] if 'trade_date' in data.columns else data.index
        result['volume'] = volume
        
        # 均量
        result['vol_ma'] = self._calculate_ma(volume, self.ma_period)
        
        # 量比 = 当日成交量 / MA5均量
        result['vol_ratio'] = volume / result['vol_ma']
        
        # 换手率（如果有）
        if 'turn' in data.columns:
            result['turn'] = data['turn']
        
        # 缩量天数统计（连续成交量低于均量）
        result['low_vol_days'] = self._count_low_vol_days(volume, result['vol_ma'].values)
        
        # 放量判断（量比>2）
        result['is_high_vol'] = result['vol_ratio'] > 2
        
        # 缩量判断（量比<0.5）
        result['is_low_vol'] = result['vol_ratio'] < 0.5
        
        return result
    
    def _calculate_ma(self, data: np.ndarray, period: int) -> np.ndarray:
        """计算移动平均"""
        result = np.zeros(len(data))
        for i in range(period - 1, len(data)):
            result[i] = data[i-period+1:i+1].mean()
        # 前period-1个用已有数据均值
        for i in range(period - 1):
            result[i] = data[:i+1].mean() if i > 0 else data[0]
        return result
    
    def _count_low_vol_days(self, volume: np.ndarray, vol_ma: np.ndarray) -> np.ndarray:
        """统计连续缩量天数"""
        result = np.zeros(len(volume))
        count = 0
        for i in range(len(volume)):
            if vol_ma[i] > 0 and volume[i] < vol_ma[i] * 0.7:
                count += 1
            else:
                count = 0
            result[i] = count
        return result
    
    def get_score(self, vol_data: pd.DataFrame) -> pd.Series:
        """计算因子得分
        
        抄底评分逻辑：
        - 缩量下跌（连续3天以上缩量）: 80分（卖盘枯竭）
        - 放量下跌（恐慌抛售）: 60分
        - 正常成交量: 40分
        - 放量上涨: 70分（确认底部）
        
        Args:
            vol_data: 成交量计算结果
            
        Returns:
            得分序列
        """
        low_vol_days = vol_data['low_vol_days']
        vol_ratio = vol_data['vol_ratio']
        
        score = pd.Series(40.0, index=vol_data.index)
        
        # 连续缩量天数越多，卖盘越枯竭，得分越高
        score.loc[low_vol_days >= 5] = 90
        score.loc[(low_vol_days >= 3) & (low_vol_days < 5)] = 80
        score.loc[(low_vol_days >= 1) & (low_vol_days < 3)] = 60
        
        # 放量（量比>2）
        score.loc[vol_ratio > 2] = 70
        
        # 极缩量（量比<0.3）
        score.loc[vol_ratio < 0.3] = 85
        
        return score
    
    @property
    def weight(self) -> float:
        return 0.15