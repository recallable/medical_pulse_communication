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
    access_token: str
    token_type: str = "bearer"


class UserInfo(BaseModel):
    id: int
    username: str
    phone: Optional[str] = None
    is_active: bool
    is_certified: bool


class UserLoginResponse(BaseModel):
    token: TokenData
    user: UserInfo
