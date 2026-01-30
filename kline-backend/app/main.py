"""FastAPI主入口"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.api.endpoints import stock, kline
from app.core.ssh_tunnel import tunnel_manager
from app.db.clickhouse import db_client
from app.db.redis import redis_client


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时
    print("正在启动服务...")

    # 启动SSH隧道（失败不阻塞）
    try:
        tunnel_manager.start()
    except Exception as e:
        print(f"SSH隧道启动失败: {e}")

    # 连接数据库（失败不阻塞）
    try:
        db_client.connect()
    except Exception as e:
        print(f"ClickHouse连接失败: {e}")

    # 连接Redis（失败不阻塞）
    try:
        redis_client.connect()
    except Exception as e:
        print(f"Redis连接失败: {e}")

    print("服务启动完成")

    yield

    # 关闭时
    print("正在关闭服务...")
    try:
        tunnel_manager.stop()
    except:
        pass
    try:
        db_client.close()
    except:
        pass
    try:
        redis_client.close()
    except:
        pass
    print("服务已关闭")


# 创建FastAPI应用
app = FastAPI(
    title="K线图API",
    description="股票K线图数据API服务",
    version="1.0.0",
    lifespan=lifespan
)

# 配置CORS（允许前端跨域访问）
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
