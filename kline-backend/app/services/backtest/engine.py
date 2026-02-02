"""回测引擎"""
from typing import List, Dict, Optional
from datetime import datetime
from decimal import Decimal


class Position:
    """持仓信息"""
    def __init__(self, code: str, name: str, shares: int, avg_price: float, current_price: float):
        self.code = code
        self.name = name
        self.shares = shares
        self.avg_price = avg_price
        self.current_price = current_price
        self.market_value = shares * current_price
        self.cost = shares * avg_price
        self.profit = self.market_value - self.cost
        self.profit_pct = (self.profit / self.cost * 100) if self.cost > 0 else 0


class Trade:
    """交易记录"""
    def __init__(
        self,
        date: str,
        code: str,
        name: str,
        action: str,  # 'buy' or 'sell'
        price: float,
        shares: int,
        amount: float,
        commission: float,
        reason: str
    ):
        self.date = date
        self.code = code
        self.name = name
        self.action = action
        self.price = price
        self.shares = shares
        self.amount = amount
        self.commission = commission
        self.reason = reason


class DailyRecord:
    """每日账户记录"""
    def __init__(
        self,
        date: str,
        cash: float,
        market_value: float,
        total_value: float,
        positions: List[Position]
    ):
        self.date = date
        self.cash = cash
        self.market_value = market_value
        self.total_value = total_value
        self.positions = positions


class BacktestEngine:
    """回测引擎"""

    def __init__(
        self,
        initial_capital: float = 100000.0,
        commission_rate: float = 0.0003,  # 万三佣金
        tax_rate: float = 0.001,  # 千一印花税（仅卖出）
        min_commission: float = 5.0  # 最低佣金5元
    ):
        self.initial_capital = initial_capital
        self.commission_rate = commission_rate
        self.tax_rate = tax_rate
        self.min_commission = min_commission

        # 账户状态
        self.cash = initial_capital
        self.positions: Dict[str, Position] = {}

        # 记录
        self.trades: List[Trade] = []
        self.daily_records: List[DailyRecord] = []

    def calculate_commission(self, amount: float, is_sell: bool = False) -> float:
        """计算手续费"""
        commission = amount * self.commission_rate
        if commission < self.min_commission:
            commission = self.min_commission

        # 卖出时加印花税
        if is_sell:
            commission += amount * self.tax_rate

        return commission

    def buy(
        self,
        date: str,
        code: str,
        name: str,
        price: float,
        shares: int,
        reason: str = ""
    ) -> bool:
        """买入股票"""
        # 确保买入整百股
        shares = (shares // 100) * 100
        if shares == 0:
            return False

        amount = price * shares
        commission = self.calculate_commission(amount, is_sell=False)
        total_cost = amount + commission

        # 检查现金是否足够
        if total_cost > self.cash:
            return False

        # 扣除现金
        self.cash -= total_cost

        # 更新持仓
        if code in self.positions:
            pos = self.positions[code]
            new_shares = pos.shares + shares
            new_cost = pos.cost + amount
            pos.shares = new_shares
            pos.avg_price = new_cost / new_shares
            pos.cost = new_cost
        else:
            self.positions[code] = Position(
                code=code,
                name=name,
                shares=shares,
                avg_price=price,
                current_price=price
            )

        # 记录交易
        self.trades.append(Trade(
            date=date,
            code=code,
            name=name,
            action='buy',
            price=price,
            shares=shares,
            amount=amount,
            commission=commission,
            reason=reason
        ))

        return True

    def sell(
        self,
        date: str,
        code: str,
        name: str,
        price: float,
        shares: Optional[int] = None,
        reason: str = ""
    ) -> bool:
        """卖出股票"""
        if code not in self.positions:
            return False

        pos = self.positions[code]

        # 如果未指定卖出数量，则全部卖出
        if shares is None:
            shares = pos.shares

        # 确保卖出整百股
        shares = (shares // 100) * 100
        if shares == 0 or shares > pos.shares:
            return False

        amount = price * shares
        commission = self.calculate_commission(amount, is_sell=True)

        # 增加现金
        self.cash += (amount - commission)

        # 更新持仓
        if shares == pos.shares:
            # 全部卖出
            del self.positions[code]
        else:
            # 部分卖出
            pos.shares -= shares
            pos.cost = pos.avg_price * pos.shares

        # 记录交易
        self.trades.append(Trade(
            date=date,
            code=code,
            name=name,
            action='sell',
            price=price,
            shares=shares,
            amount=amount,
            commission=commission,
            reason=reason
        ))

        return True

    def update_prices(self, date: str, prices: Dict[str, float]):
        """更新持仓价格"""
        for code, price in prices.items():
            if code in self.positions:
                self.positions[code].current_price = price
                self.positions[code].market_value = self.positions[code].shares * price
                self.positions[code].profit = self.positions[code].market_value - self.positions[code].cost
                if self.positions[code].cost > 0:
                    self.positions[code].profit_pct = (
                        self.positions[code].profit / self.positions[code].cost * 100
                    )

    def record_daily(self, date: str):
        """记录每日账户状态"""
        market_value = sum(pos.market_value for pos in self.positions.values())
        total_value = self.cash + market_value

        self.daily_records.append(DailyRecord(
            date=date,
            cash=self.cash,
            market_value=market_value,
            total_value=total_value,
            positions=list(self.positions.values())
        ))

    def get_current_position(self, code: str) -> Optional[Position]:
        """获取当前持仓"""
        return self.positions.get(code)

    def has_position(self, code: str) -> bool:
        """是否持有某股票"""
        return code in self.positions

    def get_total_value(self) -> float:
        """获取总资产"""
        market_value = sum(pos.market_value for pos in self.positions.values())
        return self.cash + market_value
