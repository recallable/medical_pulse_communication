from typing import Type, TypeVar, AsyncGenerator

import redis.asyncio as aioredis
from fastapi import Request

from core.redis_client import redis_client_manager
from middleware.exception import BusinessException
from services.base import BaseService

T = TypeVar("T")

async def get_redis_client() -> AsyncGenerator[aioredis.Redis, None]:
    """
    依赖注入：获取 Redis 客户端实例
    """
    client = redis_client_manager.get_client()
    try:
        yield client
    finally:
        await client.close()

def get_service(service_type: Type[T]) -> T:
    """
    依赖注入：获取服务实例
    """
    def _get_service() -> T:
        return service_type()
    return _get_service

async def get_current_user_id(request: Request) -> int:
    """
    依赖项：获取当前登录用户的 ID
    必须在经过 AuthenticationMiddleware 认证的路由中使用
    """
    user_id = getattr(request.state, "user_id", None)
    
    if not user_id:
        # 理论上如果是白名单路径调用此依赖，会抛出此异常
        # 非白名单路径如果 Token 无效，在中间件层就已经被拦截了
        raise BusinessException(code=401, message="用户未登录或登录已过期")
        
    return int(user_id)
