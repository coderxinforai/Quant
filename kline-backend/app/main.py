"""FastAPI主入口"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.api.endpoints import stock, kline
from app.core.ssh_tunnel import tunnel_manager
from app.db.clickhouse import db_client
from app.db.redis import redis_client
from app.core.logging_config import setup_logging, get_logger
from app.core.middleware import ErrorHandlerMiddleware, LoggingMiddleware

# 初始化日志系统
setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时
    logger.info("正在启动服务...")

    # 启动SSH隧道（失败不阻塞）
    try:
        tunnel_manager.start()
        logger.info("SSH隧道启动成功")
    except Exception as e:
        logger.error(f"SSH隧道启动失败: {e}", exc_info=True)

    # 连接数据库（失败不阻塞）
    try:
        db_client.connect()
        logger.info("ClickHouse连接成功")
    except Exception as e:
        logger.error(f"ClickHouse连接失败: {e}", exc_info=True)

    # 连接Redis（失败不阻塞）
    try:
        redis_client.connect()
        logger.info("Redis连接成功")
    except Exception as e:
        logger.error(f"Redis连接失败: {e}", exc_info=True)

    logger.info("服务启动完成")

    yield

    # 关闭时
    logger.info("正在关闭服务...")
    try:
        tunnel_manager.stop()
        logger.info("SSH隧道已关闭")
    except Exception as e:
        logger.error(f"SSH隧道关闭失败: {e}")
    try:
        db_client.close()
        logger.info("ClickHouse已关闭")
    except Exception as e:
        logger.error(f"ClickHouse关闭失败: {e}")
    try:
        redis_client.close()
        logger.info("Redis已关闭")
    except Exception as e:
        logger.error(f"Redis关闭失败: {e}")
    logger.info("服务已关闭")


# 创建FastAPI应用
app = FastAPI(
    title="K线图API",
    description="股票K线图数据API服务",
    version="1.0.0",
    lifespan=lifespan
)

# 配置中间件
# 注意：中间件按添加顺序的逆序执行
# 所以先添加的后执行

# 1. CORS（最后执行，最先接触响应）
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://192.168.50.90",
        "http://192.168.50.90:80"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. 错误处理中间件
app.add_middleware(ErrorHandlerMiddleware)

# 3. 日志中间件（第一个执行，记录所有请求）
app.add_middleware(LoggingMiddleware)

# 注册路由
app.include_router(stock.router, prefix="/api/stocks", tags=["stocks"])
app.include_router(kline.router, prefix="/api/kline", tags=["kline"])


@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "K线图API服务",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
async def health():
    """健康检查"""
    return {
        "status": "ok",
        "ssh_tunnel": tunnel_manager.is_alive()
    }
