"""Redis客户端"""
import redis
from app.core.config import settings


class RedisClient:
    """Redis客户端（单例）"""

    _instance = None
    _client = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def connect(self):
        """建立Redis连接"""
        if self._client is None:
            self._client = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB,
                decode_responses=True
            )
            print(f"已连接到Redis: {settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB}")
        return self._client

    def get_client(self):
        """获取客户端实例"""
        if self._client is None:
            return self.connect()
        return self._client

    def close(self):
        """关闭连接"""
        if self._client:
            self._client.close()
            self._client = None
            print("Redis连接已关闭")


# 全局单例
redis_client = RedisClient()
