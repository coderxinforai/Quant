"""回测策略"""
import pandas as pd
from typing import List, Dict, Any
from app.services.indicator_service import IndicatorService


class Signal:
    """交易信号"""
    def __init__(self, date: str, action: str, reason: str = ""):
        self.date = date
        self.action = action  # 'buy', 'sell', 'hold'
        self.reason = reason


class Strategy:
    """策略基类"""

    def __init__(self, name: str, params: Dict[str, Any]):
        self.name = name
        self.params = params

    def generate_signals(self, df: pd.DataFrame) -> List[Signal]:
        """生成交易信号（子类实现）"""
        raise NotImplementedError


class MAStrategy(Strategy):
    """均线交叉策略"""

    def __init__(self, params: Dict[str, Any]):
        super().__init__("MA均线交叉", params)
        self.fast_period = params.get('fast_period', 5)
        self.slow_period = params.get('slow_period', 20)

    def generate_signals(self, df: pd.DataFrame) -> List[Signal]:
        """
        均线交叉策略：
        - 快线上穿慢线 → 买入信号
        - 快线下穿慢线 → 卖出信号
        """
        signals = []

        # 计算均线
        indicators = IndicatorService.calculate_ma(
            df, periods=[self.fast_period, self.slow_period]
        )
        df[f'ma{self.fast_period}'] = indicators[f'ma{self.fast_period}']
        df[f'ma{self.slow_period}'] = indicators[f'ma{self.slow_period}']

        # 生成信号
        for i in range(1, len(df)):
            prev_fast = df.iloc[i-1][f'ma{self.fast_period}']
            prev_slow = df.iloc[i-1][f'ma{self.slow_period}']
            curr_fast = df.iloc[i][f'ma{self.fast_period}']
            curr_slow = df.iloc[i][f'ma{self.slow_period}']

            # 跳过空值
            if pd.isna(prev_fast) or pd.isna(prev_slow) or pd.isna(curr_fast) or pd.isna(curr_slow):
                continue

            # 金叉：快线上穿慢线
            if prev_fast <= prev_slow and curr_fast > curr_slow:
                signals.append(Signal(
                    date=df.iloc[i]['date'],
                    action='buy',
                    reason=f'MA{self.fast_period}上穿MA{self.slow_period}'
                ))
            # 死叉：快线下穿慢线
            elif prev_fast >= prev_slow and curr_fast < curr_slow:
                signals.append(Signal(
                    date=df.iloc[i]['date'],
                    action='sell',
                    reason=f'MA{self.fast_period}下穿MA{self.slow_period}'
                ))

        return signals


class MACDStrategy(Strategy):
    """MACD策略"""

    def __init__(self, params: Dict[str, Any]):
        super().__init__("MACD策略", params)
        self.fast = params.get('fast', 12)
        self.slow = params.get('slow', 26)
        self.signal = params.get('signal', 9)

    def generate_signals(self, df: pd.DataFrame) -> List[Signal]:
        """
        MACD策略：
        - DIF上穿DEA（MACD柱由负转正）→ 买入
        - DIF下穿DEA（MACD柱由正转负）→ 卖出
        """
        signals = []

        # 计算MACD
        indicators = IndicatorService.calculate_macd(
            df, fast=self.fast, slow=self.slow, signal=self.signal
        )
        df['macd_dif'] = indicators['dif']
        df['macd_dea'] = indicators['dea']
        df['macd_hist'] = indicators['hist']

        # 生成信号
        for i in range(1, len(df)):
            prev_hist = df.iloc[i-1]['macd_hist']
            curr_hist = df.iloc[i]['macd_hist']

            if pd.isna(prev_hist) or pd.isna(curr_hist):
                continue

            # MACD柱由负转正（金叉）
            if prev_hist <= 0 and curr_hist > 0:
                signals.append(Signal(
                    date=df.iloc[i]['date'],
                    action='buy',
                    reason='MACD金叉'
                ))
            # MACD柱由正转负（死叉）
            elif prev_hist >= 0 and curr_hist < 0:
                signals.append(Signal(
                    date=df.iloc[i]['date'],
                    action='sell',
                    reason='MACD死叉'
                ))

        return signals


class KDJStrategy(Strategy):
    """KDJ策略"""

    def __init__(self, params: Dict[str, Any]):
        super().__init__("KDJ策略", params)
        self.n = params.get('n', 9)
        self.m1 = params.get('m1', 3)
        self.m2 = params.get('m2', 3)
        self.oversold = params.get('oversold', 20)
        self.overbought = params.get('overbought', 80)

    def generate_signals(self, df: pd.DataFrame) -> List[Signal]:
        """
        KDJ策略：
        - J值从超卖区上穿K值 → 买入
        - J值从超买区下穿K值 → 卖出
        """
        signals = []

        # 计算KDJ
        indicators = IndicatorService.calculate_kdj(
            df, n=self.n, m1=self.m1, m2=self.m2
        )
        df['kdj_k'] = indicators['k']
        df['kdj_d'] = indicators['d']
        df['kdj_j'] = indicators['j']

        # 生成信号
        for i in range(1, len(df)):
            prev_k = df.iloc[i-1]['kdj_k']
            prev_j = df.iloc[i-1]['kdj_j']
            curr_k = df.iloc[i]['kdj_k']
            curr_j = df.iloc[i]['kdj_j']

            if pd.isna(prev_k) or pd.isna(prev_j) or pd.isna(curr_k) or pd.isna(curr_j):
                continue

            # J值从超卖区上穿K值
            if prev_j < self.oversold and prev_j <= prev_k and curr_j > curr_k:
                signals.append(Signal(
                    date=df.iloc[i]['date'],
                    action='buy',
                    reason=f'KDJ超卖反弹(J={curr_j:.1f})'
                ))
            # J值从超买区下穿K值
            elif prev_j > self.overbought and prev_j >= prev_k and curr_j < curr_k:
                signals.append(Signal(
                    date=df.iloc[i]['date'],
                    action='sell',
                    reason=f'KDJ超买回落(J={curr_j:.1f})'
                ))

        return signals


class RSIStrategy(Strategy):
    """RSI策略"""

    def __init__(self, params: Dict[str, Any]):
        super().__init__("RSI策略", params)
        self.period = params.get('period', 14)
        self.oversold = params.get('oversold', 30)
        self.overbought = params.get('overbought', 70)

    def generate_signals(self, df: pd.DataFrame) -> List[Signal]:
        """
        RSI策略：
        - RSI从超卖区向上突破 → 买入
        - RSI从超买区向下突破 → 卖出
        """
        signals = []

        # 计算RSI
        indicators = IndicatorService.calculate_rsi(df, periods=[self.period])
        df[f'rsi{self.period}'] = indicators[f'rsi{self.period}']

        # 生成信号
        for i in range(1, len(df)):
            prev_rsi = df.iloc[i-1][f'rsi{self.period}']
            curr_rsi = df.iloc[i][f'rsi{self.period}']

            if pd.isna(prev_rsi) or pd.isna(curr_rsi):
                continue

            # 从超卖区向上突破
            if prev_rsi < self.oversold and curr_rsi >= self.oversold:
                signals.append(Signal(
                    date=df.iloc[i]['date'],
                    action='buy',
                    reason=f'RSI超卖反弹(RSI={curr_rsi:.1f})'
                ))
            # 从超买区向下突破
            elif prev_rsi > self.overbought and curr_rsi <= self.overbought:
                signals.append(Signal(
                    date=df.iloc[i]['date'],
                    action='sell',
                    reason=f'RSI超买回落(RSI={curr_rsi:.1f})'
                ))

        return signals


class BOLLStrategy(Strategy):
    """布林带策略"""

    def __init__(self, params: Dict[str, Any]):
        super().__init__("布林带策略", params)
        self.n = params.get('n', 20)
        self.k = params.get('k', 2)

    def generate_signals(self, df: pd.DataFrame) -> List[Signal]:
        """
        布林带策略：
        - 价格从下轨反弹向上突破 → 买入
        - 价格从上轨回落向下突破 → 卖出
        """
        signals = []

        # 计算布林带
        indicators = IndicatorService.calculate_boll(df, n=self.n, k=self.k)
        df['boll_mid'] = indicators['mid']
        df['boll_upper'] = indicators['upper']
        df['boll_lower'] = indicators['lower']

        # 生成信号
        for i in range(1, len(df)):
            prev_close = df.iloc[i-1]['close']
            curr_close = df.iloc[i]['close']
            prev_lower = df.iloc[i-1]['boll_lower']
            curr_lower = df.iloc[i]['boll_lower']
            prev_upper = df.iloc[i-1]['boll_upper']
            curr_upper = df.iloc[i]['boll_upper']

            if pd.isna(prev_lower) or pd.isna(curr_lower) or pd.isna(prev_upper) or pd.isna(curr_upper):
                continue

            # 价格从下轨反弹
            if prev_close <= prev_lower and curr_close > curr_lower:
                signals.append(Signal(
                    date=df.iloc[i]['date'],
                    action='buy',
                    reason='触及布林下轨反弹'
                ))
            # 价格从上轨回落
            elif prev_close >= prev_upper and curr_close < curr_upper:
                signals.append(Signal(
                    date=df.iloc[i]['date'],
                    action='sell',
                    reason='触及布林上轨回落'
                ))

        return signals


class StrategyFactory:
    """策略工厂"""

    @staticmethod
    def get_strategy_definitions() -> List[Dict[str, Any]]:
        """获取所有策略定义"""
        return [
            {
                "id": "ma_cross",
                "name": "MA均线交叉",
                "description": "快线上穿慢线买入，下穿卖出",
                "params": [
                    {
                        "name": "fast_period",
                        "label": "快线周期",
                        "type": "number",
                        "default": 5,
                        "min": 2,
                        "max": 60
                    },
                    {
                        "name": "slow_period",
                        "label": "慢线周期",
                        "type": "number",
                        "default": 20,
                        "min": 5,
                        "max": 120
                    }
                ]
            },
            {
                "id": "macd",
                "name": "MACD策略",
                "description": "MACD金叉买入，死叉卖出",
                "params": [
                    {
                        "name": "fast",
                        "label": "快线EMA周期",
                        "type": "number",
                        "default": 12,
                        "min": 5,
                        "max": 30
                    },
                    {
                        "name": "slow",
                        "label": "慢线EMA周期",
                        "type": "number",
                        "default": 26,
                        "min": 10,
                        "max": 60
                    },
                    {
                        "name": "signal",
                        "label": "信号线周期",
                        "type": "number",
                        "default": 9,
                        "min": 3,
                        "max": 20
                    }
                ]
            },
            {
                "id": "kdj",
                "name": "KDJ策略",
                "description": "KDJ超卖反弹买入，超买回落卖出",
                "params": [
                    {
                        "name": "n",
                        "label": "RSV周期",
                        "type": "number",
                        "default": 9,
                        "min": 3,
                        "max": 30
                    },
                    {
                        "name": "m1",
                        "label": "K平滑周期",
                        "type": "number",
                        "default": 3,
                        "min": 1,
                        "max": 10
                    },
                    {
                        "name": "m2",
                        "label": "D平滑周期",
                        "type": "number",
                        "default": 3,
                        "min": 1,
                        "max": 10
                    },
                    {
                        "name": "oversold",
                        "label": "超卖线",
                        "type": "number",
                        "default": 20,
                        "min": 10,
                        "max": 40
                    },
                    {
                        "name": "overbought",
                        "label": "超买线",
                        "type": "number",
                        "default": 80,
                        "min": 60,
                        "max": 90
                    }
                ]
            },
            {
                "id": "rsi",
                "name": "RSI策略",
                "description": "RSI超卖反弹买入，超买回落卖出",
                "params": [
                    {
                        "name": "period",
                        "label": "RSI周期",
                        "type": "number",
                        "default": 14,
                        "min": 5,
                        "max": 30
                    },
                    {
                        "name": "oversold",
                        "label": "超卖线",
                        "type": "number",
                        "default": 30,
                        "min": 20,
                        "max": 40
                    },
                    {
                        "name": "overbought",
                        "label": "超买线",
                        "type": "number",
                        "default": 70,
                        "min": 60,
                        "max": 80
                    }
                ]
            },
            {
                "id": "boll",
                "name": "布林带策略",
                "description": "价格触及下轨反弹买入，触及上轨回落卖出",
                "params": [
                    {
                        "name": "n",
                        "label": "均线周期",
                        "type": "number",
                        "default": 20,
                        "min": 10,
                        "max": 60
                    },
                    {
                        "name": "k",
                        "label": "标准差倍数",
                        "type": "number",
                        "default": 2,
                        "min": 1,
                        "max": 3,
                        "step": 0.1
                    }
                ]
            }
        ]

    @staticmethod
    def create_strategy(strategy_id: str, params: Dict[str, Any]) -> Strategy:
        """创建策略实例"""
        strategies = {
            "ma_cross": MAStrategy,
            "macd": MACDStrategy,
            "kdj": KDJStrategy,
            "rsi": RSIStrategy,
            "boll": BOLLStrategy
        }

        strategy_class = strategies.get(strategy_id)
        if not strategy_class:
            raise ValueError(f"Unknown strategy: {strategy_id}")

        return strategy_class(params)
