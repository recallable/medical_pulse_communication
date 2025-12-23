from fastapi import APIRouter, UploadFile, Request, File as UploadFileParam

from models.schemas.user import UserLoginRequest
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


@user_router.post('/identity/ocr')
async def uploader_ocr(
        request: Request,
        side: str = 'front',
        file: UploadFile = UploadFileParam(..., description="上传的文件"), ):
    result = await user_service.uploader_ocr(request,side, file)
    return APIResponse(data=result)
