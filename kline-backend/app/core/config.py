from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # SSH隧道配置
    SSH_HOST: str = "wsl"
    SSH_LOCAL_PORT: int = 18123
    SSH_REMOTE_PORT: int = 8123

    # ClickHouse配置
    CH_HOST: str = "localhost"
    CH_PORT: int = 18123
    CH_DATABASE: str = "stock"
    CH_USER: str = "default"
    CH_PASSWORD: str = ""

    # Redis配置
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: str = ""

    # 服务配置
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
