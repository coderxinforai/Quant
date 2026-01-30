"""股票服务"""
from typing import Optional
from app.db.clickhouse import ClickHouseClient
from app.schemas.stock import StockListResponse, StockInfo


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
        if keyword:
            # 使用HAVING子句进行过滤
            query = f"""
                SELECT
                    code,
                    any(name) AS name,
                    count() AS records
                FROM stock.minute_kline
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
                FROM stock.minute_kline
                GROUP BY code
                ORDER BY code
                LIMIT {limit}
            """

        df = self.db.query_df(query)

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
        query = f"""
            SELECT name
            FROM stock.minute_kline
            WHERE code = '{code}'
            LIMIT 1
        """
        result = self.db.query(query)
        if result.result_rows:
            return result.result_rows[0][0]
        return code
