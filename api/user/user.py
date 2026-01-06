from celery.result import AsyncResult
from fastapi import APIRouter, UploadFile, Request, File as UploadFileParam, Depends

from core.deps import get_current_user_id
from middleware.exception import BusinessException
from models.schemas.user import UserLoginRequest, RefreshTokenRequest
from services.user import user_service
from utils.response import APIResponse

user_router = APIRouter(prefix='/user')



@user_router.post('/login')
async def login(
        login_data: UserLoginRequest
):
    """
    用户登录接口
    """
    result = await user_service.login(login_data)
    return APIResponse.success(data=result)


@user_router.post('/refresh-token')
async def refresh_token(
        request: RefreshTokenRequest
):
    """
    刷新 Token 接口
    """
    result = await user_service.refresh_token(request.refresh_token)
    return APIResponse.success(data=result)


@user_router.post('/identity/ocr')
async def uploader_ocr(
        request: Request,
        side: str = 'front',
        file: UploadFile = UploadFileParam(..., description="上传的文件"), ):
    user_id = getattr(request.state, "user_id", None)

    from core import celery_app
    task = celery_app.baidu_ocr_task.apply_async((user_id, side, file,))
    # result = await user_service.uploader_ocr(user_id, side, file)
    return APIResponse(data={"task_id": task.id, 'message': '识别中...'})
    # return APIResponse(data=result)


@user_router.get('/identity/ocr/status/{task_id}')
async def get_ocr_result(task_id: str):
    # 通过 task_id 去 Redis 里查结果
    from core.celery_app import celery_app
    res = AsyncResult(task_id, app=celery_app)

    # 1. 任务还在排队或处理中
    if not res.ready():
        return APIResponse(data={
            "status": "PENDING",
            "info": "正在识别中..."
        })

    # 2. 任务执行成功
    if res.successful():
        result_data = res.result  # 这里就是 baidu_ocr_task 返回的 return result
        return APIResponse(data={
            "status": "SUCCESS",
            "data": result_data  # 包含姓名、身份证号等信息
        })

    # 3. 任务执行失败
    else:
        return APIResponse(code=500, message="识别失败", data={
            "status": "FAILURE",
            "error": str(res.result)
        })


@user_router.post('/certification')
async def certification(
        request: Request
):
    """
    用户认证接口
    """
    user_id = getattr(request.state, "user_id", None)
    if not user_id:
        raise BusinessException(message="用户未登录", code=401)
    result = await user_service.certification(user_id)
    return APIResponse.success(data=result)


@user_router.get('/friendships')
async def get_friendships(
        user_id: int = Depends(get_current_user_id)
):
    """
    获取用户好友列表
    """

    result = await user_service.get_friendships(user_id)
    return APIResponse.success(data=result)
