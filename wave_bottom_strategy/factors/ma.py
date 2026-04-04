# -*- coding: utf-8 -*-
"""均线因子 - 权重15%"""

from typing import Dict, Any, List
import pandas as pd
import numpy as np

try:
    import talib
    HAS_TALIB = True
except ImportError:
    HAS_TALIB = False

from .base import Factor
from utils.logger import get_logger

logger = get_logger('ma_factor')


class MAFactor(Factor):
    """移动平均线因子
    
    参数:
        periods: 均线周期列表，默认 [5, 20, 60]
    
    抄底信号:
        - 价格低于所有均线: 弱势，但可能接近底部
        - MA5上穿MA20: 短期转强信号
        - 价格接近MA60: 重要支撑位
    """
    
    def __init__(self, params: Dict[str, Any] = None):
        super().__init__(params)
        self.periods = self.params.get('periods', [5, 20, 60])
    
    def calculate(self, data: pd.DataFrame) -> pd.DataFrame:
        """计算均线值
        
        Args:
            data: 日K线数据
            
        Returns:
            包含各均线值的DataFrame
        """
        close = data['close'].values
        
        result = pd.DataFrame()
        result['trade_date'] = data['trade_date'] if 'trade_date' in data.columns else data.index
        result['close'] = close
        
        for period in self.periods:
            if HAS_TALIB:
                ma = talib.MA(close, timeperiod=period, matype=0)
            else:
                ma = self._calculate_ma_manual(close, period)
            
            result[f'ma{period}'] = ma
        
        # 计算均线偏离度
        result['bias_ma5'] = (close - result['ma5']) / result['ma5'] * 100
        result['bias_ma20'] = (close - result['ma20']) / result['ma20'] * 100
        result['bias_ma60'] = (close - result['ma60']) / result['ma60'] * 100
        
        return result
    
    def _calculate_ma_manual(self, data: np.ndarray, period: int) -> np.ndarray:
        """手动计算均线"""
        result = np.zeros(len(data))
        for i in range(period - 1, len(data)):
            result[i] = data[i-period+1:i+1].mean()
        return result
    
    def get_score(self, ma_data: pd.DataFrame) -> pd.Series:
        """计算因子得分
        
        抄底评分逻辑：
        - 价格低于MA60超过20%: 可能超跌，80分
        - 价格低于MA60 10-20%: 偏弱，60分
        - 价格接近MA60: 支撑位，50分
        - 价格高于MA60: 正常或强势，30分
        
        Args:
            ma_data: 均线计算结果
            
        Returns:
            得分序列
        """
        bias_ma60 = ma_data['bias_ma60']
        
        score = pd.Series(30.0, index=ma_data.index)
        
        # 抄底评分（偏离度负值越大，可能越接近底部）
        score.loc[bias_ma60 < -20] = 80  # 大幅跌破MA60
        score.loc[(bias_ma60 >= -20) & (bias_ma60 < -10)] = 60
        score.loc[(bias_ma60 >= -10) & (bias_ma60 < -5)] = 50
        score.loc[(bias_ma60 >= -5) & (bias_ma60 < 0)] = 40
        
        return score
    
    def get_signal(self, ma_data: pd.DataFrame) -> pd.Series:
        """生成信号
        
        Args:
            ma_data: 均线计算结果
            
        Returns:
            信号序列
        """
        ma5 = ma_data['ma5']
        ma20 = ma_data['ma20']
        
        signal = pd.Series(0, index=ma_data.index)
        
        # MA5上穿MA20
        for i in range(1, len(ma5)):
            if ma5.iloc[i] > ma20.iloc[i] and ma5.iloc[i-1] <= ma20.iloc[i-1]:
                signal.iloc[i] = 1
        
        return signal
    
    @property
    def weight(self) -> float:
        return 0.15