"""股票对比 API"""
from fastapi import APIRouter, Query, HTTPException
from typing import List, Optional
from app.db.clickhouse import db_client
from app.services.kline_service import KLineService
from app.core.logging_config import get_logger

logger = get_logger(__name__)

router = APIRouter()


@router.get("/data")
async def get_compare_data(
    codes: str = Query(..., description="股票代码列表，逗号分隔，最多5只"),
    start_date: str = Query(..., description="开始日期 YYYY-MM-DD"),
    end_date: str = Query(..., description="结束日期 YYYY-MM-DD"),
    period: str = Query("day", description="K线周期"),
    mode: str = Query("change_pct", description="对比模式: change_pct(涨跌幅) 或 price(价格)"),
):
    """
    获取多股票对比数据

    Args:
        codes: 股票代码列表，逗号分隔（如：000001.SZ,600000.SH）
        start_date: 开始日期
        end_date: 结束日期
        period: K线周期
        mode: 对比模式

    Returns:
        对比数据（归一化处理）
    """
    logger.info(f"股票对比请求: codes={codes}, start={start_date}, end={end_date}, period={period}, mode={mode}")

    # 解析股票代码列表
    code_list = [c.strip() for c in codes.split(',') if c.strip()]

    # 验证股票数量
    if len(code_list) == 0:
        raise HTTPException(status_code=400, detail="至少需要选择1只股票")
    if len(code_list) > 5:
        raise HTTPException(status_code=400, detail="最多支持5只股票对比")

    kline_service = KLineService(db_client)

    result = {
        "stocks": [],
        "dates": [],
        "series": []
    }

    try:
        # 获取每只股票的K线数据
        for code in code_list:
            try:
                kline_response = kline_service.get_kline(
                    code=code,
                    start_date=start_date,
                    end_date=end_date,
                    adj_type='after',  # 使用后复权进行对比
                    period=period
                )

                if len(kline_response.klines) == 0:
                    logger.warning(f"股票 {code} 没有数据")
                    continue

                # 提取日期和价格
                dates = [k.date for k in kline_response.klines]
                prices = [k.close for k in kline_response.klines]

                # 计算涨跌幅（归一化）
                if mode == 'change_pct' and len(prices) > 0:
                    base_price = prices[0]
                    values = [((p - base_price) / base_price * 100) for p in prices]
                else:
                    values = prices

                # 添加到结果
                stock_data = {
                    "code": code,
                    "name": kline_response.stock_info.name,
                    "dates": dates,
                    "values": values
                }
                result["stocks"].append(stock_data)

                # 更新统一的日期列表（使用第一只股票的日期）
                if len(result["dates"]) == 0:
                    result["dates"] = dates

            except Exception as e:
                logger.error(f"获取股票 {code} 数据失败: {str(e)}")
                continue

        # 构建 series 格式（便于前端图表使用）
        for stock in result["stocks"]:
            result["series"].append({
                "name": f"{stock['name']} ({stock['code']})",
                "data": stock["values"]
            })

        logger.info(f"对比数据准备完成: {len(result['stocks'])} 只股票")

        return {
            "code": 0,
            "message": "success",
            "data": result
        }

    except Exception as e:
        logger.error(f"股票对比失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"服务器错误: {str(e)}")
