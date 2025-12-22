from contextlib import asynccontextmanager

from fastapi import FastAPI
from tortoise.contrib.fastapi import register_tortoise

from api.router import api_router
from core.config import settings
from middleware.authentication import register_authentication_middleware
from middleware.exception import register_exception_middleware
from middleware.logging import register_access_log_middleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    pass


# app = FastAPI(lifespan=lifespan)
app = FastAPI()
app.include_router(api_router)

register_exception_middleware(app)
register_access_log_middleware(app)
register_authentication_middleware(app)
register_tortoise(
    app,
    config=settings.tortoise_config,
    add_exception_handlers=True,
)
