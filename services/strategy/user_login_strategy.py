import hashlib
from abc import ABC, abstractmethod
from typing import Any, Dict
from urllib.parse import quote

import httpx
import requests
from tortoise import timezone
from tortoise.transactions import in_transaction

from core.config import Settings, settings
from models.entity.user import User, UserThirdParty
from models.schemas.user import UserLoginRequest
from crud.user import user_crud
from utils.password_utils import PasswordUtil
from middleware.exception import BusinessException
from core.redis_client import redis_client_manager


class LoginStrategy(ABC):
    _kwargs: Dict[str, Any] = {}

    # 1. 定义一个非抽象的模板方法，作为对外入口
    async def execute(self, login_data: UserLoginRequest) -> User:
        """
        模板方法：定义登录的标准骨架
        """
        # 步骤1：前置检查
        await self.before_check(login_data)

        # 步骤2：执行具体登录逻辑（由子类实现）
        user = await self._login(login_data)

        # 步骤3：后置处理
        await self.after_login(user)

        return user

    @abstractmethod
    async def _login(self, login_data: UserLoginRequest) -> User:
        pass

    @abstractmethod
    async def before_check(self, login_data: UserLoginRequest):
        """
        登录前检查
        :param login_data: 登录请求数据
        """
        pass

    @abstractmethod
    async def after_login(self, user: User) -> User:
        """
        登录后处理
        :param user: 用户对象
        """
        pass


class AccountLoginStrategy(LoginStrategy):
    """
    账号密码登录策略
    """

    async def after_login(self, user: User) -> User:
        pass

    async def before_check(self, login_data: UserLoginRequest):
        if not login_data.username or not login_data.password:
            raise BusinessException(message="用户名和密码不能为空", code=400)

    async def _login(self, login_data: UserLoginRequest) -> User:
        # 1. 尝试用户名登录
        user = await user_crud.get_by_username(login_data.username)

        if not user:
            # 2. 尝试手机号登录
            user = await user_crud.get_by_phone(login_data.username)
            if not user:
                raise BusinessException(message="用户名或密码错误", code=400)

        # 3. 验证密码
        if not hashlib.sha256(login_data.password.encode()).hexdigest() == user.password:
            raise BusinessException(message="用户名或密码错误", code=400)

        return user


class PhoneSmsLoginStrategy(LoginStrategy):
    """
    短信验证码登录策略
    """

    async def before_check(self, login_data: UserLoginRequest):
        if not login_data.phone or not login_data.code:
            raise BusinessException(message="手机号和验证码不能为空", code=400)

            # 1. 验证短信验证码
        redis = redis_client_manager.get_client()
        try:
            cached_code = await redis.get(f"sms_code:{login_data.phone}")
            if not cached_code or cached_code != login_data.code:
                raise BusinessException(message="验证码错误或已过期", code=400)

            # 验证成功后删除验证码 (可选，视业务需求而定)
            await redis.delete(f"sms_code:{login_data.phone}")
        finally:
            await redis.close()

    async def after_login(self, kwargs: Dict[str, Any]) -> User:
        pass

    async def _login(self, login_data: UserLoginRequest) -> User:

        # 2. 查询用户
        user = await user_crud.get_by_phone(login_data.phone)
        if not user:
            raise BusinessException(message="该手机号未注册", code=400)

        return user


class DingTalkLoginStrategy(LoginStrategy):
    """
    钉钉登录策略
    """

    async def before_check(self, login_data: UserLoginRequest):
        if not login_data.code:
            raise BusinessException(message="钉钉授权码不能为空", code=400)

    async def after_login(self, user: User) -> User:
        pass

    async def _login(self, login_data: UserLoginRequest) -> User:
        """
        钉钉登录核心逻辑：获取信息 -> 查找用户 -> (不存在则注册) -> 绑定 -> 返回用户
        """

        # 1. 获取钉钉用户信息 (使用 httpx 异步)
        ding_info = await self._fetch_ding_user_info(login_data.code)

        ding_openid = ding_info.get("openId")
        ding_unionid = ding_info.get("unionId")  # 最好存 unionId
        phone = ding_info.get("mobile")
        nickname = ding_info.get("nick")

        if not phone:
            raise BusinessException(message="无法获取钉钉手机号，请检查权限配置", code=400)

        # 2. 核心业务：查找或注册 (建议加事务锁)
        async with in_transaction():
            # A. 先看这个钉钉 openid 是否已经绑定了用户
            third_party = await UserThirdParty.filter(third_openid=ding_openid,
                                                      third_platform="dingtalk").select_related("user").first()

            if third_party and third_party.user:
                return third_party.user

            # B. 如果没绑定，通过手机号查找主账号
            user = await User.filter(phone=phone).first()

            if not user:
                # C. 如果主账号也不存在 -> 注册新用户
                user = await User.create(
                    username=nickname if nickname else f"ding_{ding_openid[-6:]}",
                    phone=phone,
                    # password=... (第三方登录通常设一个随机不可用的密码 或 留空)
                    status=1,
                    last_login_time=timezone.now()
                )

            # D. 绑定关联关系 (无论是新注册的还是已有的，只要没绑定过，都绑定一下)
            if not third_party:
                await UserThirdParty.create(
                    user=user,
                    third_platform="dingtalk",
                    third_openid=ding_openid,
                    third_unionid=ding_unionid
                )
            else:
                # 理论上不会走到这，除非脏数据(有third_party但没user)，修复一下
                third_party.user = user
                await third_party.save()

        return user

    async def _fetch_ding_user_info(self, code: str) -> dict:
        """独立出来的网络请求方法"""
        async with httpx.AsyncClient() as client:
            # 1. 获取 AccessToken
            token_url = 'https://api.dingtalk.com/v1.0/oauth2/userAccessToken'
            token_payload = {
                "clientId": settings.dingtalk_client_id,
                "clientSecret": settings.dingtalk_client_secret,
                "code": code,
                "grantType": "authorization_code"
            }
            token_resp = await client.post(token_url, json=token_payload)
            token_data = token_resp.json()

            access_token = token_data.get('accessToken')
            if not access_token:
                raise BusinessException(message=f"钉钉登录失败: {token_data.get('message')}")

            # 2. 获取用户信息
            info_url = 'https://api.dingtalk.com/v1.0/contact/users/me'
            headers = {"x-acs-dingtalk-access-token": access_token}
            info_resp = await client.get(info_url, headers=headers)
            return info_resp.json()


class LoginStrategyFactory:
    """
    登录策略工厂
    """
    _strategies = {
        "account": AccountLoginStrategy(),
        "dingtalk": DingTalkLoginStrategy(),
        "phone": PhoneSmsLoginStrategy()
    }

    @classmethod
    def get_strategy(cls, login_type: str) -> LoginStrategy:
        """
        获取登录策略
        :param login_type: 登录类型
        :return: 登录策略对象
        """
        strategy = cls._strategies.get(login_type)
        if not strategy:
            raise BusinessException(code=400, message=f"不支持的登录方式: {login_type}")
        return strategy
