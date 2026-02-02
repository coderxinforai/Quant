"""回测绩效指标计算"""
import math
from typing import List
from .engine import DailyRecord, Trade


class BacktestMetrics:
    """回测绩效指标"""

    def __init__(
        self,
        daily_records: List[DailyRecord],
        trades: List[Trade],
        initial_capital: float
    ):
        self.daily_records = daily_records
        self.trades = trades
        self.initial_capital = initial_capital

        # 计算指标（注意顺序：先计算基础数据，再计算依赖它们的指标）
        self.total_trades = len([t for t in trades if t.action == 'buy'])
        self.win_trades = self._count_win_trades()
        self.loss_trades = self.total_trades - self.win_trades

        self.total_return = self._calculate_total_return()
        self.annual_return = self._calculate_annual_return()
        self.max_drawdown = self._calculate_max_drawdown()
        self.sharpe_ratio = self._calculate_sharpe_ratio()
        self.win_rate = self._calculate_win_rate()
        self.profit_loss_ratio = self._calculate_profit_loss_ratio()

    def _calculate_total_return(self) -> float:
        """计算总收益率"""
        if not self.daily_records:
            return 0.0

        final_value = self.daily_records[-1].total_value
        return (final_value - self.initial_capital) / self.initial_capital * 100

    def _calculate_annual_return(self) -> float:
        """计算年化收益率"""
        if not self.daily_records or len(self.daily_records) < 2:
            return 0.0

        days = len(self.daily_records)
        years = days / 252  # 一年约252个交易日

        if years <= 0:
            return 0.0

        final_value = self.daily_records[-1].total_value
        return (pow(final_value / self.initial_capital, 1 / years) - 1) * 100

    def _calculate_max_drawdown(self) -> float:
        """计算最大回撤"""
        if not self.daily_records:
            return 0.0

        peak = self.daily_records[0].total_value
        max_dd = 0.0

        for record in self.daily_records:
            if record.total_value > peak:
                peak = record.total_value

            dd = (peak - record.total_value) / peak * 100
            if dd > max_dd:
                max_dd = dd

        return max_dd

    def _calculate_sharpe_ratio(self, risk_free_rate: float = 0.03) -> float:
        """
        计算夏普比率
        risk_free_rate: 无风险利率（年化），默认3%
        """
        if not self.daily_records or len(self.daily_records) < 2:
            return 0.0

        # 计算每日收益率
        daily_returns = []
        for i in range(1, len(self.daily_records)):
            prev_value = self.daily_records[i-1].total_value
            curr_value = self.daily_records[i].total_value
            daily_return = (curr_value - prev_value) / prev_value
            daily_returns.append(daily_return)

        if not daily_returns:
            return 0.0

        # 计算平均收益率和标准差
        avg_return = sum(daily_returns) / len(daily_returns)
        variance = sum((r - avg_return) ** 2 for r in daily_returns) / len(daily_returns)
        std_dev = math.sqrt(variance)

        if std_dev == 0:
            return 0.0

        # 年化
        daily_rf_rate = risk_free_rate / 252
        sharpe = (avg_return - daily_rf_rate) / std_dev * math.sqrt(252)

        return sharpe

    def _calculate_win_rate(self) -> float:
        """计算胜率"""
        if self.total_trades == 0:
            return 0.0

        return self.win_trades / self.total_trades * 100

    def _count_win_trades(self) -> int:
        """统计盈利交易次数"""
        win_count = 0
        buy_trades = {}

        for trade in self.trades:
            if trade.action == 'buy':
                # 记录买入
                if trade.code not in buy_trades:
                    buy_trades[trade.code] = []
                buy_trades[trade.code].append(trade)
            elif trade.action == 'sell':
                # 卖出时计算盈亏
                if trade.code in buy_trades and buy_trades[trade.code]:
                    buy_trade = buy_trades[trade.code].pop(0)
                    profit = (trade.price - buy_trade.price) * trade.shares - trade.commission - buy_trade.commission
                    if profit > 0:
                        win_count += 1

        return win_count

    def _calculate_profit_loss_ratio(self) -> float:
        """计算盈亏比"""
        total_profit = 0.0
        total_loss = 0.0
        buy_trades = {}

        for trade in self.trades:
            if trade.action == 'buy':
                if trade.code not in buy_trades:
                    buy_trades[trade.code] = []
                buy_trades[trade.code].append(trade)
            elif trade.action == 'sell':
                if trade.code in buy_trades and buy_trades[trade.code]:
                    buy_trade = buy_trades[trade.code].pop(0)
                    profit = (trade.price - buy_trade.price) * trade.shares - trade.commission - buy_trade.commission
                    if profit > 0:
                        total_profit += profit
                    else:
                        total_loss += abs(profit)

        if total_loss == 0:
            return 0.0

        return total_profit / total_loss

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "total_return": round(self.total_return, 2),
            "annual_return": round(self.annual_return, 2),
            "max_drawdown": round(self.max_drawdown, 2),
            "sharpe_ratio": round(self.sharpe_ratio, 2),
            "win_rate": round(self.win_rate, 2),
            "profit_loss_ratio": round(self.profit_loss_ratio, 2),
            "total_trades": self.total_trades,
            "win_trades": self.win_trades,
            "loss_trades": self.loss_trades
        }
