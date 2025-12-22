from fastapi import APIRouter
from fastapi.params import Query

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


@user_router.get('/callback')
async def callback(code: str = Query(..., description='钉钉授权码')):
    login_data = UserLoginRequest(code=code, login_type='dingtalk')
    return APIResponse.success(data=await user_service.login(login_data))
