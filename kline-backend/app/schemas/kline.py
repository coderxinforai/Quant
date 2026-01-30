"""K线相关Schema"""
from pydantic import BaseModel
from typing import List


class KLineData(BaseModel):
    """单根K线数据"""
    date: str
    open: float
    close: float
    high: float
    low: float
    volume: float
    amount: float = 0.0


class StockBasicInfo(BaseModel):
    """股票基础信息"""
    code: str
    name: str


class KLineResponse(BaseModel):
    """K线数据响应"""
    stock_info: StockBasicInfo
    klines: List[KLineData]
    count: int
