"""技术指标计算服务"""
import pandas as pd
import numpy as np
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class IndicatorService:
    """技术指标计算服务"""

    @staticmethod
    def calculate_ma(df: pd.DataFrame, periods: list = None) -> dict:
        """
        计算移动平均线

        Args:
            df: K线数据DataFrame
            periods: 周期列表，默认 [5, 10, 20, 60]

        Returns:
            dict: {ma5: [...], ma10: [...], ...}
        """
        if periods is None:
            periods = [5, 10, 20, 60]

        result = {}
        for p in periods:
            col_name = f"ma{p}"
            ma_values = df['close'].rolling(window=p).mean()
            # 将 NaN 转换为 None (JSON中为null)
            result[col_name] = [None if pd.isna(v) else round(float(v), 2) for v in ma_values]

        return result

    @staticmethod
    def calculate_macd(df: pd.DataFrame, fast=12, slow=26, signal=9) -> dict:
        """
        计算MACD指标

        Args:
            df: K线数据DataFrame
            fast: 快线周期
            slow: 慢线周期
            signal: 信号线周期

        Returns:
            dict: {dif: [...], dea: [...], macd: [...]}
        """
        ema_fast = df['close'].ewm(span=fast, adjust=False).mean()
        ema_slow = df['close'].ewm(span=slow, adjust=False).mean()
        dif = ema_fast - ema_slow
        dea = dif.ewm(span=signal, adjust=False).mean()
        macd_hist = (dif - dea) * 2

        return {
            'dif': [None if pd.isna(v) else round(float(v), 4) for v in dif],
            'dea': [None if pd.isna(v) else round(float(v), 4) for v in dea],
            'macd': [None if pd.isna(v) else round(float(v), 4) for v in macd_hist]
        }

    @staticmethod
    def calculate_kdj(df: pd.DataFrame, n=9, m1=3, m2=3) -> dict:
        """
        计算KDJ指标

        Args:
            df: K线数据DataFrame
            n: RSV周期
            m1: K值平滑周期
            m2: D值平滑周期

        Returns:
            dict: {k: [...], d: [...], j: [...]}
        """
        low_n = df['low'].rolling(window=n).min()
        high_n = df['high'].rolling(window=n).max()

        # RSV = (收盘价 - N日最低价) / (N日最高价 - N日最低价) * 100
        rsv = (df['close'] - low_n) / (high_n - low_n) * 100
        rsv = rsv.fillna(50)  # 初始值设为50

        # K = RSV的M1日移动平均
        k = rsv.ewm(com=m1-1, adjust=False).mean()
        # D = K的M2日移动平均
        d = k.ewm(com=m2-1, adjust=False).mean()
        # J = 3K - 2D
        j = 3 * k - 2 * d

        return {
            'k': [None if pd.isna(v) else round(float(v), 2) for v in k],
            'd': [None if pd.isna(v) else round(float(v), 2) for v in d],
            'j': [None if pd.isna(v) else round(float(v), 2) for v in j]
        }

    @staticmethod
    def calculate_rsi(df: pd.DataFrame, periods: list = None) -> dict:
        """
        计算RSI指标

        Args:
            df: K线数据DataFrame
            periods: 周期列表，默认 [6, 12, 24]

        Returns:
            dict: {rsi6: [...], rsi12: [...], ...}
        """
        if periods is None:
            periods = [6, 12, 24]

        result = {}
        delta = df['close'].diff()

        for p in periods:
            gain = delta.clip(lower=0).rolling(window=p).mean()
            loss = (-delta.clip(upper=0)).rolling(window=p).mean()

            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))

            col_name = f'rsi{p}'
            result[col_name] = [None if pd.isna(v) else round(float(v), 2) for v in rsi]

        return result

    @staticmethod
    def calculate_boll(df: pd.DataFrame, n=20, k=2) -> dict:
        """
        计算布林带指标

        Args:
            df: K线数据DataFrame
            n: 移动平均周期
            k: 标准差倍数

        Returns:
            dict: {mid: [...], upper: [...], lower: [...]}
        """
        mid = df['close'].rolling(window=n).mean()
        std = df['close'].rolling(window=n).std()
        upper = mid + k * std
        lower = mid - k * std

        return {
            'mid': [None if pd.isna(v) else round(float(v), 2) for v in mid],
            'upper': [None if pd.isna(v) else round(float(v), 2) for v in upper],
            'lower': [None if pd.isna(v) else round(float(v), 2) for v in lower]
        }

    def calculate(self, df: pd.DataFrame, indicators: list) -> dict:
        """
        计算指定的指标集合

        Args:
            df: K线数据DataFrame (必须包含 open, close, high, low, volume 列)
            indicators: 指标名称列表 ['ma', 'macd', 'kdj', 'rsi', 'boll']

        Returns:
            dict: {ma: {...}, macd: {...}, ...}
        """
        result = {}

        for ind in indicators:
            try:
                if ind == 'ma':
                    result['ma'] = self.calculate_ma(df)
                    logger.info(f"计算MA指标完成")
                elif ind == 'macd':
                    result['macd'] = self.calculate_macd(df)
                    logger.info(f"计算MACD指标完成")
                elif ind == 'kdj':
                    result['kdj'] = self.calculate_kdj(df)
                    logger.info(f"计算KDJ指标完成")
                elif ind == 'rsi':
                    result['rsi'] = self.calculate_rsi(df)
                    logger.info(f"计算RSI指标完成")
                elif ind == 'boll':
                    result['boll'] = self.calculate_boll(df)
                    logger.info(f"计算BOLL指标完成")
                else:
                    logger.warning(f"未知指标: {ind}")
            except Exception as e:
                logger.error(f"计算指标 {ind} 失败: {e}", exc_info=True)

        return result
