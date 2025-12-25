from contextlib import asynccontextmanager

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from tortoise.contrib.fastapi import register_tortoise

from api.router import api_router
from core.config import settings
from core.redis_client import redis_client_manager
from middleware.authentication import register_authentication_middleware
from middleware.exception import register_exception_middleware
from middleware.logging import register_access_log_middleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时初始化 Redis 连接池
    await redis_client_manager.init_pool()
    yield
    # 关闭时释放 Redis 连接池
    await redis_client_manager.close_pool()


# app = FastAPI(lifespan=lifespan)
app = FastAPI(lifespan=lifespan)
app.include_router(api_router)

register_exception_middleware(app)
register_access_log_middleware(app)
register_authentication_middleware(app)
register_tortoise(
    app,
    config=settings.tortoise_config,
    generate_schemas=True,
    add_exception_handlers=True,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境请改为具体的域名，如 ["http://localhost:8080"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")