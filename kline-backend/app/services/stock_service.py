"""股票服务"""
from typing import Optional
from app.db.clickhouse import ClickHouseClient
from app.schemas.stock import StockListResponse, StockInfo
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class StockService:
    """股票服务"""

    def __init__(self, db: ClickHouseClient):
        self.db = db

    def search_stocks(self, keyword: Optional[str] = None, limit: int = 50) -> StockListResponse:
        """
        搜索股票列表

        Args:
            keyword: 搜索关键词（股票代码或名称）
            limit: 返回数量限制

        Returns:
            StockListResponse: 股票列表
        """
        logger.info(f"搜索股票: keyword={keyword}, limit={limit}")

        # 清理和验证关键词（防止SQL注入）
        if keyword:
            # 移除潜在的危险字符
            keyword = keyword.replace("'", "").replace(";", "").replace("--", "")

        if keyword:
            # 使用HAVING子句进行过滤
            query = f"""
                SELECT
                    code,
                    any(name) AS name,
                    count() AS records
                FROM minute_kline
                GROUP BY code
                HAVING code LIKE '%{keyword}%' OR name LIKE '%{keyword}%'
                ORDER BY code
                LIMIT {limit}
            """
        else:
            query = f"""
                SELECT
                    code,
                    any(name) AS name,
                    count() AS records
                FROM minute_kline
                GROUP BY code
                ORDER BY code
                LIMIT {limit}
            """

        logger.debug(f"执行查询: {query}")
        df = self.db.query_df(query)
        logger.info(f"查询到 {len(df)} 条股票记录")

        items = [
            StockInfo(
                code=row['code'],
                name=row['name'],
                records=row['records']
            )
            for _, row in df.iterrows()
        ]

        return StockListResponse(items=items, total=len(items))

    def get_stock_name(self, code: str) -> str:
        """
        获取股票名称

        Args:
            code: 股票代码

        Returns:
            str: 股票名称
        """
        # 清理股票代码（防止SQL注入）
        code = code.replace("'", "").replace(";", "").replace("--", "")

        query = f"""
            SELECT name
            FROM stock.minute_kline
            WHERE code = '{code}'
            LIMIT 1
        """
        logger.debug(f"查询股票名称: code={code}")
        result = self.db.query(query)
        if result.result_rows:
            name = result.result_rows[0][0]
            logger.debug(f"找到股票名称: {name}")
            return name
        logger.warning(f"未找到股票名称: code={code}")
        return code

    def get_stock_date_range(self, code: str) -> dict:
        """
        获取股票的数据时间范围

        Args:
            code: 股票代码

        Returns:
            dict: {'start_date': '2020-01-01', 'end_date': '2024-12-31'}
        """
        # 清理股票代码（防止SQL注入）
        code = code.replace("'", "").replace(";", "").replace("--", "")

        query = f"""
            SELECT
                min(trade_date) AS start_date,
                max(trade_date) AS end_date
            FROM stock.minute_kline
            WHERE code = '{code}'
        """
        logger.debug(f"查询股票日期范围: code={code}")
        result = self.db.query(query)
        if result.result_rows and result.result_rows[0][0]:
            start_date = str(result.result_rows[0][0])
            end_date = str(result.result_rows[0][1])
            logger.info(f"股票 {code} 日期范围: {start_date} ~ {end_date}")
            return {
                "start_date": start_date,
                "end_date": end_date
            }
        logger.warning(f"未找到股票 {code} 的日期范围")
        return {
            "start_date": None,
            "end_date": None
        }
