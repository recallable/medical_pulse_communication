# jwt_util.py
import jwt
import datetime
from typing import Dict, Any, Optional
from core.config import settings

class JWTUtil:
    # 从配置中读取
    SECRET_KEY = settings.secret_key
    ALGORITHM = settings.algorithm
    EXPIRE_MINUTES = settings.access_token_expire_minutes

    @classmethod
    def create_token(cls, data: Dict[str, Any], expire_minutes: Optional[int] = None) -> str:
        """生成 JWT Token"""
        expire = datetime.datetime.utcnow() + datetime.timedelta(
            minutes=expire_minutes or cls.EXPIRE_MINUTES
        )
        payload = {
            "data": data,
            "exp": expire,
            "iat": datetime.datetime.utcnow(),
        }
        return jwt.encode(payload, cls.SECRET_KEY, algorithm=cls.ALGORITHM)

    @classmethod
    def verify_token(cls, token: str) -> Optional[Dict[str, Any]]:
        """验证 JWT Token，失败则返回 None"""
        # 注意：这里我们让调用方处理具体的异常（如果需要区分过期/无效），或者简单返回 None
        # 根据中间件的需求，如果这里只返回 None，中间件就不知道具体错误原因了
        # 为了兼容中间件的细粒度错误处理，我们可以选择在这里抛出异常，或者让中间件自己捕获
        # 但考虑到工具类的通用性，这里保持原样，如果抛出异常，需要在中间件捕获
        
        # 既然中间件需要细粒度控制，我们稍微修改一下，让它抛出异常供上层捕获
        # 或者我们保持这个方法简单返回 None，但中间件可能需要区分 ExpiredSignatureError
        
        # 方案：verify_token 成功返回 dict，失败抛出原始 jwt 异常，以便中间件捕获
        payload = jwt.decode(token, cls.SECRET_KEY, algorithms=[cls.ALGORITHM])
        return payload.get("data")

    @classmethod
    def refresh_token(cls, token: str) -> Optional[str]:
        """刷新 token，生成新的 token"""
        try:
            data = cls.verify_token(token)
            return cls.create_token(data)
        except Exception:
            return None

    @classmethod
    def get_raw_payload(cls, token: str) -> Optional[Dict[str, Any]]:
        """解析原始 payload，不校验签名（慎用）"""
        try:
            return jwt.decode(token, options={"verify_signature": False})
        except Exception:
            return None
