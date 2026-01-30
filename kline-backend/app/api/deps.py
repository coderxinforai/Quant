"""依赖注入"""
from app.db.clickhouse import db_client
from app.services.cache_service import CacheService


def get_db():
    """获取数据库客户端"""
    return db_client


def get_cache():
    """获取缓存服务"""
    return CacheService()
