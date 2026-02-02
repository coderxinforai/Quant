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

    def _get_period_group_by(self, period: str) -> tuple:
        """
        根据周期返回 GROUP BY 表达式和 SELECT 表达式

        Args:
            period: K线周期 'day'/'week'/'month'/'year'

        Returns:
            tuple: (group_by_expr, select_expr)
        """
        if period == 'week':
            return "toMonday(trade_date)", "toMonday(trade_date) AS trade_date"
        elif period == 'month':
            return "toStartOfMonth(trade_date)", "toStartOfMonth(trade_date) AS trade_date"
        elif period == 'year':
            return "toStartOfYear(trade_date)", "toStartOfYear(trade_date) AS trade_date"
        else:  # day
            return "trade_date", "trade_date"

    def get_kline(
        self,
        code: str,
        start_date: str,
        end_date: str,
        adj_type: str = 'none',
        period: str = 'day'
    ) -> KLineResponse:
        """
        获取K线数据（通用周期）

        Args:
            code: 股票代码
            start_date: 开始日期 YYYY-MM-DD
            end_date: 结束日期 YYYY-MM-DD
            adj_type: 复权类型
            period: K线周期 'day'/'week'/'month'/'year'

        Returns:
            KLineResponse: K线数据
        """
        logger.info(f"获取K线数据: code={code}, start={start_date}, end={end_date}, adj_type={adj_type}, period={period}")

        # 清理参数（防止SQL注入）
        code = code.replace("'", "").replace(";", "").replace("--", "")
        start_date = start_date.replace("'", "").replace(";", "").replace("--", "")
        end_date = end_date.replace("'", "").replace(";", "").replace("--", "")

        # 获取价格列和周期分组表达式
        price_cols = self._get_price_columns(adj_type)
        group_by_expr, select_expr = self._get_period_group_by(period)

        # 构建查询SQL
        query = f"""
            SELECT
                {select_expr},
                {price_cols},
                sum(volume) AS volume,
                sum(amount) AS amount
            FROM minute_kline
            WHERE code = '{code}'
              AND trade_date >= '{start_date}'
              AND trade_date <= '{end_date}'
            GROUP BY {group_by_expr}
            ORDER BY trade_date
        """

        logger.debug(f"执行查询: {query[:200]}...")
        df = self.db.query_df(query)

        if df.empty:
            logger.warning(f"未找到数据: code={code}, start={start_date}, end={end_date}, period={period}")
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
            count=len(klines),
            period=period
        )

    def get_daily_kline(
        self,
        code: str,
        start_date: str,
        end_date: str,
        adj_type: str = 'none'
    ) -> KLineResponse:
        """
        获取日K线数据（向后兼容方法，代理到 get_kline）

        Args:
            code: 股票代码
            start_date: 开始日期 YYYY-MM-DD
            end_date: 结束日期 YYYY-MM-DD
            adj_type: 复权类型

        Returns:
            KLineResponse: K线数据
        """
        return self.get_kline(code, start_date, end_date, adj_type, period='day')

    def get_minute_kline(
        self,
        code: str,
        trade_date: str,
        interval: int = 1,
        adj_type: str = 'none'
    ) -> KLineResponse:
        """
        获取分钟级K线数据

        Args:
            code: 股票代码
            trade_date: 交易日期 YYYY-MM-DD
            interval: 分钟间隔 1/5/15/30/60
            adj_type: 复权类型

        Returns:
            KLineResponse: K线数据
        """
        logger.info(f"获取分钟K线: code={code}, date={trade_date}, interval={interval}, adj_type={adj_type}")

        # 清理参数
        code = code.replace("'", "").replace(";", "").replace("--", "")
        trade_date = trade_date.replace("'", "").replace(";", "").replace("--", "")

        # 根据复权类型选择价格列
        if adj_type == 'after':
            price_cols = """
                adj_open_after AS open,
                adj_close_after AS close,
                adj_high_after AS high,
                adj_low_after AS low
            """
        elif adj_type == 'before':
            price_cols = """
                adj_open_before AS open,
                adj_close_before AS close,
                adj_high_before AS high,
                adj_low_before AS low
            """
        else:
            price_cols = """
                open,
                close,
                high,
                low
            """

        if interval == 1:
            # 1分钟K线：直接查询
            query = f"""
                SELECT
                    dt,
                    {price_cols},
                    volume,
                    amount
                FROM minute_kline
                WHERE code = '{code}'
                  AND trade_date = '{trade_date}'
                ORDER BY dt
            """
        else:
            # 5/15/30/60分钟：按时间窗口聚合
            # 使用与日K线相同的聚合方式
            price_agg_cols = self._get_price_columns(adj_type)
            query = f"""
                SELECT
                    toStartOfInterval(dt, INTERVAL {interval} MINUTE) AS dt,
                    {price_agg_cols},
                    sum(volume) AS volume,
                    sum(amount) AS amount
                FROM minute_kline
                WHERE code = '{code}'
                  AND trade_date = '{trade_date}'
                GROUP BY toStartOfInterval(dt, INTERVAL {interval} MINUTE)
                ORDER BY dt
            """

        logger.debug(f"执行查询: {query[:200]}...")
        df = self.db.query_df(query)

        if df.empty:
            logger.warning(f"未找到数据: code={code}, date={trade_date}, interval={interval}")
            raise ValueError(f"未找到股票 {code} 在 {trade_date} 的{interval}分钟K线数据")

        # 获取股票名称
        stock_service = StockService(self.db)
        stock_name = stock_service.get_stock_name(code)

        # 转换为Pydantic模型
        klines = [
            KLineData(
                date=str(row['dt']),  # 分钟K线保留完整时间
                open=float(row['open']),
                close=float(row['close']),
                high=float(row['high']),
                low=float(row['low']),
                volume=float(row['volume']),
                amount=float(row['amount'])
            )
            for _, row in df.iterrows()
        ]

        logger.info(f"成功获取 {len(klines)} 条分钟K线数据")

        return KLineResponse(
            stock_info=StockBasicInfo(code=code, name=stock_name),
            klines=klines,
            count=len(klines),
            period=f"{interval}min"
        )
