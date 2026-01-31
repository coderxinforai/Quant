"""K线服务"""
from app.db.clickhouse import ClickHouseClient
from app.schemas.kline import KLineResponse, KLineData, StockBasicInfo
from app.services.stock_service import StockService
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class KLineService:
    """K线服务"""

    def __init__(self, db: ClickHouseClient):
        self.db = db

    def _get_price_columns(self, adj_type: str) -> str:
        """
        获取价格列SQL

        Args:
            adj_type: 复权类型 'after'=后复权, 'before'=前复权, 'none'=不复权

        Returns:
            str: SQL价格列定义
        """
        if adj_type == 'after':
            return """
                argMin(adj_open_after, dt) AS open,
                argMax(adj_close_after, dt) AS close,
                max(adj_high_after) AS high,
                min(adj_low_after) AS low
            """
        elif adj_type == 'before':
            return """
                argMin(adj_open_before, dt) AS open,
                argMax(adj_close_before, dt) AS close,
                max(adj_high_before) AS high,
                min(adj_low_before) AS low
            """
        else:  # none
            return """
                argMin(open, dt) AS open,
                argMax(close, dt) AS close,
                max(high) AS high,
                min(low) AS low
            """

    def get_daily_kline(
        self,
        code: str,
        start_date: str,
        end_date: str,
        adj_type: str = 'none'
    ) -> KLineResponse:
        """
        获取日K线数据

        Args:
            code: 股票代码
            start_date: 开始日期 YYYY-MM-DD
            end_date: 结束日期 YYYY-MM-DD
            adj_type: 复权类型

        Returns:
            KLineResponse: K线数据
        """
        logger.info(f"获取K线数据: code={code}, start={start_date}, end={end_date}, adj_type={adj_type}")

        # 清理参数（防止SQL注入）
        code = code.replace("'", "").replace(";", "").replace("--", "")
        start_date = start_date.replace("'", "").replace(";", "").replace("--", "")
        end_date = end_date.replace("'", "").replace(";", "").replace("--", "")

        # 获取价格列
        price_cols = self._get_price_columns(adj_type)

        # 构建查询SQL（从plot_kline_ssh.py复用）
        query = f"""
            SELECT
                trade_date,
                {price_cols},
                sum(volume) AS volume,
                sum(amount) AS amount
            FROM stock.minute_kline
            WHERE code = '{code}'
              AND trade_date >= '{start_date}'
              AND trade_date <= '{end_date}'
            GROUP BY trade_date
            ORDER BY trade_date
        """

        logger.debug(f"执行查询: {query[:200]}...")
        df = self.db.query_df(query)

        if df.empty:
            logger.warning(f"未找到数据: code={code}, start={start_date}, end={end_date}")
            raise ValueError(f"未找到股票 {code} 在 {start_date} 至 {end_date} 的数据")

        # 获取股票名称
        stock_service = StockService(self.db)
        stock_name = stock_service.get_stock_name(code)

        # 转换为Pydantic模型
        klines = [
            KLineData(
                date=str(row['trade_date'])[:10],  # 只取日期部分 YYYY-MM-DD
                open=float(row['open']),
                close=float(row['close']),
                high=float(row['high']),
                low=float(row['low']),
                volume=float(row['volume']),
                amount=float(row['amount'])
            )
            for _, row in df.iterrows()
        ]

        logger.info(f"成功获取 {len(klines)} 条K线数据")

        return KLineResponse(
            stock_info=StockBasicInfo(code=code, name=stock_name),
            klines=klines,
            count=len(klines)
        )
