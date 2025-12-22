from middleware.exception import BusinessException
from models.entity.user import User
from models.schemas.user import UserLoginRequest, UserLoginResponse, UserInfo, TokenData
from services.base import BaseService
from services.strategy.user_login_strategy import LoginStrategyFactory
from utils.jwt_utils import JWTUtil


class UserService(BaseService[User]):
    model = User

    async def login(self, login_data: UserLoginRequest) -> UserLoginResponse:
        """
        验证用户登录并返回 Token 和用户信息 (兼容旧接口命名)
        """
        return await self.authenticate(login_data)

    async def authenticate(self, login_data: UserLoginRequest) -> UserLoginResponse:
        """
        验证用户登录并返回 Token 和用户信息
        """
        # 1. 获取登录策略并执行登录
        strategy = LoginStrategyFactory.get_strategy(login_data.login_type)
        user: User = await strategy.execute(login_data)

        # 2. 检查激活状态
        if user.user_status == 0:
            raise BusinessException(message="该账号已被禁用", code=400)

        # 3. 生成 Token
        # JWTUtil.create_token 接受一个 dict 作为数据
        token_payload = {
            "sub": str(user.id),
            "username": user.username,
            "scope": "user"
        }
        access_token = JWTUtil.create_token(data=token_payload)

        # 4. 构造响应
        return UserLoginResponse(
            token=TokenData(access_token=access_token),
            user=UserInfo(
                id=user.id,
                username=user.username,
                phone=user.phone,
                is_active=user.user_status == 1,
            )
        )


user_service = UserService()
