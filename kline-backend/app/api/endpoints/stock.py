"""股票API端点"""
from fastapi import APIRouter, Query, Depends
from app.api.deps import get_db
from app.db.clickhouse import ClickHouseClient
from app.services.stock_service import StockService
from app.schemas.stock import StockListResponse


router = APIRouter()


@router.get("/list", response_model=dict)
async def list_stocks(
    keyword: str = Query(None, description="搜索关键词（股票代码或名称）"),
    limit: int = Query(50, le=100, description="返回数量限制"),
    db: ClickHouseClient = Depends(get_db)
):
    """
    获取股票列表

    Args:
        keyword: 搜索关键词
        limit: 返回数量限制（最大100）

    Returns:
        股票列表
    """
    service = StockService(db)
    stocks = service.search_stocks(keyword, limit)

    return {
        "code": 0,
        "message": "success",
        "data": stocks.dict()
    }
