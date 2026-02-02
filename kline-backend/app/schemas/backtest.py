"""回测相关的 Pydantic 模型"""
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional


class BacktestRequest(BaseModel):
    """回测请求"""
    code: str = Field(..., description="股票代码")
    start_date: str = Field(..., description="回测开始日期 YYYY-MM-DD")
    end_date: str = Field(..., description="回测结束日期 YYYY-MM-DD")
    strategy_id: str = Field(..., description="策略ID")
    strategy_params: Dict[str, Any] = Field(default_factory=dict, description="策略参数")
    initial_capital: float = Field(100000.0, description="初始资金")
    position_ratio: float = Field(0.8, description="单次买入仓位比例（0-1）")


class TradeRecord(BaseModel):
    """交易记录"""
    date: str
    code: str
    name: str
    action: str
    price: float
    shares: int
    amount: float
    commission: float
    reason: str


class PositionInfo(BaseModel):
    """持仓信息"""
    code: str
    name: str
    shares: int
    avg_price: float
    current_price: float
    market_value: float
    cost: float
    profit: float
    profit_pct: float


class DailyPosition(BaseModel):
    """每日持仓"""
    date: str
    cash: float
    market_value: float
    total_value: float
    positions: List[PositionInfo]


class BacktestMetricsData(BaseModel):
    """回测绩效指标"""
    total_return: float = Field(..., description="总收益率(%)")
    annual_return: float = Field(..., description="年化收益率(%)")
    max_drawdown: float = Field(..., description="最大回撤(%)")
    sharpe_ratio: float = Field(..., description="夏普比率")
    win_rate: float = Field(..., description="胜率(%)")
    profit_loss_ratio: float = Field(..., description="盈亏比")
    total_trades: int = Field(..., description="总交易次数")
    win_trades: int = Field(..., description="盈利次数")
    loss_trades: int = Field(..., description="亏损次数")
    buy_hold_return: Optional[float] = Field(None, description="买入持有收益率(%)")
    excess_return: Optional[float] = Field(None, description="超额收益(%)")


class BacktestData(BaseModel):
    """回测结果数据"""
    stock_code: str
    stock_name: str
    start_date: str
    end_date: str
    strategy_name: str
    strategy_params: Dict[str, Any]
    initial_capital: float
    final_capital: float
    metrics: BacktestMetricsData
    daily_records: List[DailyPosition]
    trades: List[TradeRecord]
    equity_curve: List[Dict[str, Any]]  # 资金曲线 [{date, value}, ...]
    buy_hold_curve: Optional[List[Dict[str, Any]]] = None  # 买入持有基准曲线


class BacktestResponse(BaseModel):
    """回测响应"""
    code: int = 0
    message: str = "success"
    data: Optional[BacktestData] = None


class StrategyParam(BaseModel):
    """策略参数定义"""
    name: str
    label: str
    type: str
    default: Any
    min: Optional[float] = None
    max: Optional[float] = None
    step: Optional[float] = None


class StrategyDefinition(BaseModel):
    """策略定义"""
    id: str
    name: str
    description: str
    params: List[StrategyParam]


class StrategyListResponse(BaseModel):
    """策略列表响应"""
    code: int = 0
    message: str = "success"
    data: List[StrategyDefinition]
