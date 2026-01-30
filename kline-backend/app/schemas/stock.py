"""股票相关Schema"""
from pydantic import BaseModel
from typing import List


class StockInfo(BaseModel):
    """股票信息"""
    code: str
    name: str
    records: int


class StockListResponse(BaseModel):
    """股票列表响应"""
    items: List[StockInfo]
    total: int
