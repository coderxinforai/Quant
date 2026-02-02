"""K线API端点"""
from fastapi import APIRouter, Query, Depends, HTTPException
from app.api.deps import get_db, get_cache
from app.db.clickhouse import ClickHouseClient
from app.services.kline_service import KLineService
from app.services.cache_service import CacheService
from app.services.indicator_service import IndicatorService
import pandas as pd


router = APIRouter()


@router.get("/data", response_model=dict)
async def get_kline_data(
    code: str = Query(..., description="股票代码，如 600000.SH"),
    start_date: str = Query(..., description="开始日期 YYYY-MM-DD"),
    end_date: str = Query(..., description="结束日期 YYYY-MM-DD"),
    adj_type: str = Query("none", description="复权类型: after=后复权, before=前复权, none=不复权"),
    period: str = Query("day", description="K线周期: day=日K, week=周K, month=月K, year=年K"),
    indicators: str = Query("", description="技术指标，逗号分隔: ma,macd,kdj,rsi,boll"),
    db: ClickHouseClient = Depends(get_db),
    cache: CacheService = Depends(get_cache)
):
    """
    获取K线数据

    Args:
        code: 股票代码
        start_date: 开始日期
        end_date: 结束日期
        adj_type: 复权类型
        period: K线周期
        indicators: 技术指标

    Returns:
        K线数据
    """
    # 解析指标列表
    ind_list = [i.strip() for i in indicators.split(',') if i.strip()] if indicators else []
    ind_key = ','.join(sorted(ind_list)) if ind_list else 'none'

    # 1. 检查缓存
    cache_key = f"kline:{code}:{period}:{start_date}:{end_date}:{adj_type}:ind_{ind_key}"
    cached = cache.get(cache_key)
    if cached:
        return cached

    try:
        # 2. 查询数据库
        service = KLineService(db)
        data = service.get_kline(code, start_date, end_date, adj_type, period)

        # 3. 计算技术指标
        if ind_list:
            # 将K线数据转换为DataFrame
            kline_dicts = [k.dict() for k in data.klines]
            df = pd.DataFrame(kline_dicts)

            # 计算指标
            indicator_service = IndicatorService()
            indicators_data = indicator_service.calculate(df, ind_list)

            # 将指标数据附加到响应中
            data.indicators = indicators_data

        # 4. 构建响应
        response = {
            "code": 0,
            "message": "success",
            "data": data.dict()
        }

        # 5. 写入缓存（根据数据日期动态设置TTL）
        ttl = cache.calculate_ttl(end_date)
        cache.set(cache_key, response, ttl)

        return response

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"服务器错误: {str(e)}")


@router.get("/minute", response_model=dict)
async def get_minute_kline(
    code: str = Query(..., description="股票代码，如 600000.SH"),
    trade_date: str = Query(..., description="交易日期 YYYY-MM-DD"),
    interval: int = Query(1, description="分钟间隔: 1/5/15/30/60"),
    adj_type: str = Query("none", description="复权类型: after=后复权, before=前复权, none=不复权"),
    db: ClickHouseClient = Depends(get_db),
    cache: CacheService = Depends(get_cache)
):
    """
    获取分钟级K线数据

    Args:
        code: 股票代码
        trade_date: 交易日期
        interval: 分钟间隔
        adj_type: 复权类型

    Returns:
        分钟K线数据
    """
    # 1. 检查缓存
    cache_key = f"kline:{code}:min{interval}:{trade_date}:{adj_type}"
    cached = cache.get(cache_key)
    if cached:
        return cached

    try:
        # 2. 查询数据库
        service = KLineService(db)
        data = service.get_minute_kline(code, trade_date, interval, adj_type)

        # 3. 构建响应
        response = {
            "code": 0,
            "message": "success",
            "data": data.dict()
        }

        # 4. 写入缓存
        # 分钟K线缓存策略：当天数据60秒，历史数据24小时
        from datetime import datetime
        trade_dt = datetime.strptime(trade_date, '%Y-%m-%d')
        today = datetime.now()
        if (today - trade_dt).days == 0:
            ttl = 60  # 当天数据1分钟
        else:
            ttl = 24 * 3600  # 历史数据24小时

        cache.set(cache_key, response, ttl)

        return response

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"服务器错误: {str(e)}")
