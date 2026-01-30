"""K线API端点"""
from fastapi import APIRouter, Query, Depends, HTTPException
from app.api.deps import get_db, get_cache
from app.db.clickhouse import ClickHouseClient
from app.services.kline_service import KLineService
from app.services.cache_service import CacheService


router = APIRouter()


@router.get("/data", response_model=dict)
async def get_kline_data(
    code: str = Query(..., description="股票代码，如 600000.SH"),
    start_date: str = Query(..., description="开始日期 YYYY-MM-DD"),
    end_date: str = Query(..., description="结束日期 YYYY-MM-DD"),
    adj_type: str = Query("none", description="复权类型: after=后复权, before=前复权, none=不复权"),
    db: ClickHouseClient = Depends(get_db),
    cache: CacheService = Depends(get_cache)
):
    """
    获取日K线数据

    Args:
        code: 股票代码
        start_date: 开始日期
        end_date: 结束日期
        adj_type: 复权类型

    Returns:
        K线数据
    """
    # 1. 检查缓存
    cache_key = f"kline:{code}:day:{start_date}:{end_date}:{adj_type}"
    cached = cache.get(cache_key)
    if cached:
        return cached

    try:
        # 2. 查询数据库
        service = KLineService(db)
        data = service.get_daily_kline(code, start_date, end_date, adj_type)

        # 3. 构建响应
        response = {
            "code": 0,
            "message": "success",
            "data": data.dict()
        }

        # 4. 写入缓存（根据数据日期动态设置TTL）
        ttl = cache.calculate_ttl(end_date)
        cache.set(cache_key, response, ttl)

        return response

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"服务器错误: {str(e)}")
