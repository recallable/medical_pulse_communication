from typing import Type, TypeVar, AsyncGenerator

import redis.asyncio as aioredis
from fastapi import Request
from fastapi import WebSocket, Query, status
from jwt import InvalidTokenError, ExpiredSignatureError

from core.redis_client import redis_client_manager
from middleware.exception import BusinessException
from utils.jwt_utils import JWTUtil

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


async def get_current_user(request: Request) -> dict:
    """
    依赖项：获取当前登录用户信息
    返回包含 user_id 的字典
    """
    user_id = getattr(request.state, "user_id", None)

    if not user_id:
        raise BusinessException(code=401, message="用户未登录或登录已过期")

    return {"user_id": int(user_id)}


async def validate_ws_token(
        websocket: WebSocket,
        token: str = Query(None)  # 从 URL 参数 ?token=xxx 获取
):
    """
    WebSocket 专用鉴权依赖
    """
    # 1. 检查 Token 是否存在
    if not token:
        # 拒绝连接：策略违规 (1008)
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return None

    try:
        # 2. 验证 Token (复用你的 JWTUtil)
        payload_data = JWTUtil.verify_token(token)

        if payload_data is None:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return None

        # 返回解析出的 user_id 或整个 payload，供路由使用
        return payload_data.get("sub")

    except (ExpiredSignatureError, InvalidTokenError):
        # Token 过期或无效，直接关闭连接
        print("WS Auth Failed: Invalid/Expired Token")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return None
    except Exception as e:
        print(f"WS Auth Error: {e}")
        await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
        return None
