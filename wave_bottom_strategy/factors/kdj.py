# -*- coding: utf-8 -*-
"""KDJ因子 - 核心因子权重45%"""

from typing import Dict, Any
import pandas as pd
import numpy as np

try:
    import talib
    HAS_TALIB = True
except ImportError:
    HAS_TALIB = False

from .base import Factor
from wave_bottom_strategy.utils.logger import get_logger

logger = get_logger('kdj_factor')


class KDJFactor(Factor):
    """KDJ随机指标因子
    
    抄底核心指标，超卖信号强
    
    参数:
        n: KDJ周期，默?
        m1: K值平滑周期，默认3
        m2: D值平滑周期，默认3
    
    抄底信号:
        - K < 20: 超卖区域
        - D < 20: 超卖确认
        - J < 20: 强超?
        - K上穿D: 金叉买入信号
    """
    
    def __init__(self, params: Dict[str, Any] = None):
        super().__init__(params)
        self.n = self.params.get('n', 9)
        self.m1 = self.params.get('m1', 3)
        self.m2 = self.params.get('m2', 3)
    
    def calculate(self, data: pd.DataFrame) -> pd.DataFrame:
        """计算KDJ?
        
        Args:
            data: 日K线数据，需包含 high, low, close
            
        Returns:
            包含K, D, J值的DataFrame
        """
        if not self.validate_data(data):
            logger.error("数据验证失败")
            return pd.DataFrame()
        
        high = data['high'].values
        low = data['low'].values
        close = data['close'].values
        
        if HAS_TALIB:
            # 使用talib计算STOCH（KDJ?
            k, d = talib.STOCH(
                high, low, close,
                fastk_period=self.n,
                slowk_period=self.m1,
                slowk_matype=0,
                slowd_period=self.m2,
                slowd_matype=0
            )
        else:
            # 手动计算KDJ
            k, d = self._calculate_kdj_manual(high, low, close)
        
        # 计算J?= 3K - 2D
        j = 3 * k - 2 * d
        
        result = pd.DataFrame({
            'trade_date': data['trade_date'] if 'trade_date' in data.columns else data.index,
            'k': k,
            'd': d,
            'j': j
        })
        
        return result
    
    def _calculate_kdj_manual(
        self,
        high: np.ndarray,
        low: np.ndarray,
        close: np.ndarray
    ) -> tuple:
        """手动计算KDJ（无talib时使用）
        
        Args:
            high: 最高价数组
            low: 最低价数组
            close: 收盘价数?
            
        Returns:
            (K, D) 数组
        """
        n = self.n
        
        # RSV = (Close - LowN) / (HighN - LowN) * 100
        rsv = np.zeros(len(close))
        
        for i in range(n - 1, len(close)):
            high_n = high[i-n+1:i+1].max()
            low_n = low[i-n+1:i+1].min()
            
            if high_n != low_n:
                rsv[i] = (close[i] - low_n) / (high_n - low_n) * 100
            else:
                rsv[i] = 50  # 防止除零
        
        # K = SMA(RSV, m1)
        k = self._sma(rsv, self.m1)
        
        # D = SMA(K, m2)
        d = self._sma(k, self.m2)
        
        return k, d
    
    def _sma(self, data: np.ndarray, period: int) -> np.ndarray:
        """简单移动平?
        
        Args:
            data: 数据数组
            period: 周期
            
        Returns:
            SMA数组
        """
        result = np.zeros(len(data))
        result[period-1] = data[:period].mean()
        
        for i in range(period, len(data)):
            result[i] = (result[i-1] * (period - 1) + data[i]) / period
        
        return result
    
    def get_score(self, kdj_data: pd.DataFrame) -> pd.Series:
        """计算因子得分?-100?
        
        抄底得分逻辑?
        - J < 10: 100分（强超卖）
        - J < 20: 80分（超卖?
        - J < 30: 60分（偏超卖）
        - J 30-50: 40分（中性偏弱）
        - J 50-80: 20分（正常?
        - J > 80: 10分（超买，不抄底?
        
        Args:
            kdj_data: KDJ计算结果
            
        Returns:
            得分序列
        """
        j = kdj_data['j']
        
        score = pd.Series(0.0, index=kdj_data.index)
        
        # 抄底评分（J值越低，得分越高?
        score.loc[j < 10] = 100
        score.loc[(j >= 10) & (j < 20)] = 80
        score.loc[(j >= 20) & (j < 30)] = 60
        score.loc[(j >= 30) & (j < 50)] = 40
        score.loc[(j >= 50) & (j < 80)] = 20
        score.loc[j >= 80] = 10
        
        return score
    
    def get_signal(self, kdj_data: pd.DataFrame) -> pd.Series:
        """生成买卖信号
        
        Args:
            kdj_data: KDJ计算结果
            
        Returns:
            信号序列 (1买入, 0持有, -1卖出)
        """
        k = kdj_data['k']
        d = kdj_data['d']
        j = kdj_data['j']
        
        signal = pd.Series(0, index=kdj_data.index)
        
        # 金叉买入信号：K上穿D ?在超卖区?
        for i in range(1, len(k)):
            if k.iloc[i] > d.iloc[i] and k.iloc[i-1] <= d.iloc[i-1]:
                if k.iloc[i] < 30:  # 在超卖区域金?
                    signal.iloc[i] = 1
        
        # 死叉卖出信号：K下穿D ?在超买区?
        for i in range(1, len(k)):
            if k.iloc[i] < d.iloc[i] and k.iloc[i-1] >= d.iloc[i-1]:
                if k.iloc[i] > 70:  # 在超买区域死?
                    signal.iloc[i] = -1
        
        return signal
    
    @property
    def weight(self) -> float:
        return 0.45  # 45% 权重
