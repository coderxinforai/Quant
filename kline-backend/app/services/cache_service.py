"""缓存服务"""
import json
from datetime import datetime
from app.db.redis import redis_client


class CacheService:
    """缓存服务"""

    def __init__(self):
        self.redis = redis_client.get_client()

    def get(self, key: str):
        """获取缓存"""
        try:
            value = self.redis.get(key)
            if value:
                return json.loads(value)
        except Exception as e:
            print(f"缓存读取失败: {e}")
        return None

    def set(self, key: str, value: dict, ttl: int = 3600):
        """设置缓存"""
        try:
            self.redis.setex(key, ttl, json.dumps(value))
        except Exception as e:
            print(f"缓存写入失败: {e}")

    def delete(self, key: str):
        """删除缓存"""
        try:
            self.redis.delete(key)
        except Exception as e:
            print(f"缓存删除失败: {e}")

    def calculate_ttl(self, end_date: str) -> int:
        """
        根据数据日期计算TTL
        历史数据缓存时间更长，当日数据缓存时间更短
        """
        try:
            end = datetime.strptime(end_date, '%Y-%m-%d')
            days_ago = (datetime.now() - end).days

            if days_ago > 30:
                return 24 * 3600  # 历史数据：24小时
            elif days_ago > 1:
                return 3600       # 近期数据：1小时
            else:
                return 300        # 当日数据：5分钟
        except:
            return 3600  # 默认1小时
