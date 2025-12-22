from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse
from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from middleware.logging import logger
from utils.response import APIResponse


class BusinessException(Exception):
    """
    业务异常类，用于表示业务逻辑中的异常情况。
    包含异常消息和异常码。
    """

    def __init__(self, message: str, code: int = 500):
        self.message = message
        self.code = code


class ExceptionHandlerMiddleware(BaseHTTPMiddleware):
    """
    异常处理中间件，用于捕获并处理应用程序中的异常。
    包含对 HTTPException、RequestValidationError 和其他异常的处理。
    """

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint):
        """
        处理请求的主要逻辑。
        尝试调用下一个中间件或路由处理函数。
        如果捕获到 HTTPException、RequestValidationError 或其他异常，
        则根据异常类型返回相应的 JSON 响应。
        """
        try:
            return await call_next(request)
        except HTTPException as e:
            logger.error(e)
            return JSONResponse(APIResponse.error(message=str(e.detail), code=e.status_code), status_code=e.status_code)
        except BusinessException as e:
            logger.warning(f"BusinessException: {e.message}")
            return JSONResponse(APIResponse.error(message=e.message, code=e.code), status_code=200) # 业务异常通常返回 200，通过 code 区分，或者返回 400
        except RequestValidationError as e:
            logger.error(e.errors())
            return JSONResponse(APIResponse.error(message=e.errors(), code=422),
                                status_code=422)
        except Exception as e:
            logger.error(e)
            return JSONResponse(APIResponse.error(message=f"internal error:{e}", code=500), status_code=500)


def register_exception_middleware(app: FastAPI):
    app.add_middleware(ExceptionHandlerMiddleware)
