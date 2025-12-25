import jwt
from fastapi import FastAPI
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse

from middleware.logging import logger
from utils.jwt_utils import JWTUtil
from utils.response import APIResponse

# 白名单路径列表 (不需要认证的接口)
WHITE_LIST = [
    "/docs",
    "/redoc",
    "/openapi.json",
    "/health",
    "/api/v1/user/login",
    "/api/v1/user/register",
    "/api/v1/user/callback",
    "/api/v1/user/send-sms",
    "/ws/chat"
]


class AuthenticationMiddleware(BaseHTTPMiddleware):
    """
    认证中间件，用于验证请求是否包含有效的 JWT 令牌。
    如果请求路径在白名单中，或请求头中包含有效的 Authorization 头，
    则继续处理请求；否则，抛出 BusinessException 异常。
    """

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint):
        """
        处理请求的主要逻辑。
        如果请求路径在白名单中，或请求头中包含有效的 Authorization 头，
        则继续处理请求；否则，抛出 BusinessException 异常。
        """
        path = request.url.path

        # 1. 检查是否在白名单中
        # 允许白名单完全匹配 或 前缀匹配 (例如 /docs, /openapi.json)
        if any(path.startswith(white_path) for white_path in WHITE_LIST):
            return await call_next(request)

        if request.scope["type"] == "websocket":
            return await call_next(request)

        # 2. 获取 Authorization 头
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            logger.warning(
                f"Authentication failed: Missing Authorization Header. Path: {path}, IP: {request.client.host if request.client else 'Unknown'}")
            return JSONResponse(status_code=401,
                                content=APIResponse.error(message="Missing Authorization Header", code=401))

            # 3. 判断 链接方式

        scheme, _, token = auth_header.partition(" ")

        # 4. 检查 Bearer 前缀
        if scheme.lower() != "bearer" or not token:
            logger.warning(
                f"Authentication failed: Invalid Authorization Scheme. Path: {path}, Header: {auth_header[:20]}...")
            return JSONResponse(status_code=401,
                                content=APIResponse.error(message="Invalid Authorization Scheme", code=401))

            # 5. 验证 Token
        try:
            # 使用 JWTUtil 验证 Token
            # 注意：JWTUtil.verify_token 会抛出 jwt 异常，需要在这里捕获
            payload_data = JWTUtil.verify_token(token)

            # 确保 payload_data 存在
            if payload_data is None:
                raise jwt.InvalidTokenError("Token payload is empty")

            # 将用户信息注入到 request.state 中
            # 假设 payload_data 结构为 {"sub": user_id, "scope": scope} 或直接就是用户信息
            # 根据 JWTUtil.create_token 的实现，payload 是 {"data": data, ...}
            # verify_token 返回的是 data 部分

            request.state.user_id = payload_data.get("sub")
            request.state.scope = payload_data.get("scope")

        except jwt.ExpiredSignatureError:
            logger.warning(f"Authentication failed: Token Expired. Path: {path}")
            return JSONResponse(status_code=401,
                                content=APIResponse.error(message="Token Expired", code=401))
        except jwt.InvalidTokenError as e:
            logger.warning(f"Authentication failed: Invalid Token. Path: {path}, Error: {str(e)}")
            return JSONResponse(status_code=401,
                                content=APIResponse.error(message="Invalid Token", code=401))
        except Exception as e:
            logger.error(f"Authentication failed: Unexpected Error. Path: {path}, Error: {str(e)}", exc_info=True)
            return JSONResponse(status_code=401,
                                content=APIResponse.error(message=f"Authentication Failed: {str(e)}", code=401))

        return await call_next(request)


def register_authentication_middleware(app: FastAPI):
    app.add_middleware(AuthenticationMiddleware)
