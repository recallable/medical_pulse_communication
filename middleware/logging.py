import logging
import os
import sys
import time
from logging.handlers import TimedRotatingFileHandler

from fastapi import Request, FastAPI
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

# 确保日志目录存在
log_dir = "logs"
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

# 配置日志格式
log_formatter = logging.Formatter(
    '%(asctime)s - [%(threadName)s] - %(name)s - %(levelname)s - %(message)s'
)

# 创建 logger
logger = logging.getLogger("api")
logger.setLevel(logging.INFO)

# 清除现有的 handlers，避免重复添加
if logger.hasHandlers():
    logger.handlers.clear()

# 控制台 Handler
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(log_formatter)
logger.addHandler(console_handler)

# 文件 Handler (按天轮转)
file_handler = TimedRotatingFileHandler(
    filename=os.path.join(log_dir, "app.log"),
    when="midnight",
    interval=1,
    backupCount=30,  # 保留30天的日志
    encoding="utf-8"
)
file_handler.setFormatter(log_formatter)
logger.addHandler(file_handler)


class AccessLogHandlerMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint):
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time

        log_params = {
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "client_ip": request.client.host if request.client else "unknown",
            "process_time": f"{process_time:.3f}s"
        }

        logger.info(
            f"{log_params['method']} {log_params['path']} "
            f"Status: {log_params['status_code']} "
            f"IP: {log_params['client_ip']} "
            f"Time: {log_params['process_time']}"
        )

        return response


def register_access_log_middleware(app: FastAPI):
    app.add_middleware(AccessLogHandlerMiddleware)
