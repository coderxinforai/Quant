"""中间件"""
import time
import traceback
from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """统一错误处理中间件"""

    async def dispatch(self, request: Request, call_next):
        try:
            response = await call_next(request)
            return response
        except Exception as exc:
            # 记录错误日志
            logger.error(
                f"请求处理异常: {request.method} {request.url.path}",
                exc_info=True
            )

            # 返回统一错误响应
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "code": -1,
                    "message": "服务器内部错误",
                    "detail": str(exc) if logger.level <= 10 else None  # DEBUG模式显示详情
                }
            )


class LoggingMiddleware(BaseHTTPMiddleware):
    """请求日志中间件"""

    async def dispatch(self, request: Request, call_next):
        start_time = time.time()

        # 记录请求
        logger.info(f"请求开始: {request.method} {request.url.path}")

        try:
            response = await call_next(request)

            # 计算耗时
            process_time = time.time() - start_time

            # 记录响应
            logger.info(
                f"请求完成: {request.method} {request.url.path} "
                f"状态={response.status_code} 耗时={process_time:.3f}s"
            )

            # 添加响应头
            response.headers["X-Process-Time"] = str(process_time)

            return response
        except Exception as exc:
            process_time = time.time() - start_time
            logger.error(
                f"请求失败: {request.method} {request.url.path} "
                f"耗时={process_time:.3f}s 错误={str(exc)}"
            )
            raise
