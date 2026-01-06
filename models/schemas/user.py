from typing import Optional, Literal

from pydantic import BaseModel, Field


class UserLoginRequest(BaseModel):
    username: Optional[str] = Field(None, description="用户名 (账号登录时必填)")
    password: Optional[str] = Field(None, description="密码 (账号登录时必填)")
    phone: Optional[str] = Field(None, description="手机号 (短信登录时必填)")
    code: Optional[str] = Field(None, description="验证码 (短信|钉钉登录时必填)")
    login_type: Literal["account", "sms", "dingtalk"] = Field(...,
                                                              description="登录类型: account-账号密码, sms-短信验证码, dingtalk-钉钉登录")


class TokenData(BaseModel):
    access_token: str = Field(..., description="访问令牌")
    refresh_token: str = Field(..., description="刷新令牌")
    token_type: str = Field('bearer', description="令牌类型")


class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(..., description="刷新令牌")


class UserInfo(BaseModel):
    id: int = Field(..., description="用户ID")
    username: str = Field(..., description="用户名")
    phone: Optional[str] = Field(..., description="手机号")
    is_active: bool = Field(..., description="用户状态")
    is_certified: bool = Field(..., description="用户认证状态")
    user_identity: int = Field(..., description="用户身份: 0-普通用户, 1-医师")


class UserLoginResponse(BaseModel):
    token: TokenData = Field(..., description="用户登录凭证")
    user: UserInfo = Field(..., description="用户信息")


class UsershipsBasicResponse(BaseModel):
    # id: int = Field(..., description="用户关系ID")
    # user_id: int = Field(..., description="用户ID")
    friend_id: int = Field(..., description="好友ID")
    friend_username: str = Field(..., description="好友用户名")
