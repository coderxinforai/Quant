"""ClickHouse数据库客户端"""
import clickhouse_connect
from app.core.config import settings
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class ClickHouseClient:
    """ClickHouse客户端（单例）"""

    _instance = None
    _client = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def connect(self):
        """建立数据库连接"""
        if self._client is None:
            logger.info(f"正在连接ClickHouse数据库: {settings.CH_HOST}:{settings.CH_PORT}/{settings.CH_DATABASE}")
            self._client = clickhouse_connect.get_client(
                host=settings.CH_HOST,
                port=settings.CH_PORT,
                database=settings.CH_DATABASE,
                username=settings.CH_USER,
                password=settings.CH_PASSWORD
            )
            logger.info("ClickHouse数据库连接成功")
        return self._client

    def get_client(self):
        """获取客户端实例"""
        if self._client is None:
            return self.connect()
        return self._client

    def query_df(self, query: str):
        """执行查询并返回DataFrame"""
        client = self.get_client()
        return client.query_df(query)

    def query(self, query: str):
        """执行查询并返回原始结果"""
        client = self.get_client()
        return client.query(query)

    def close(self):
        """关闭连接"""
        if self._client:
            self._client.close()
            self._client = None
            logger.info("ClickHouse连接已关闭")


# 全局单例
db_client = ClickHouseClient()
