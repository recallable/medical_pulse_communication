import functools
import json

from fastapi import Request, HTTPException
from fastapi.encoders import jsonable_encoder

from core.redis_client import redis_client_manager


def idempotent(expire: int = 60 * 60 * 24):
    """
    幂等性装饰器
    :param expire: 幂等 Key 过期时间（秒）
    """
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # 尝试从 args 或 kwargs 中获取 Request 对象
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            if not request:
                for key, value in kwargs.items():
                    if isinstance(value, Request):
                        request = value
                        break
            
            # 如果没有找到 Request 对象，或者 Header 中没有 Idempotency-Key，则跳过幂等逻辑
            # 这里为了严格演示，如果没有 Idempotency-Key，我们就不做处理，直接执行
            idempotency_key = None
            if request:
                idempotency_key = request.headers.get("Idempotency-Key")
            
            if not idempotency_key:
                return await func(*args, **kwargs)

            redis_key = f"idempotency:{idempotency_key}"
            client = redis_client_manager.get_client()

            # 尝试加锁
            # SET key value NX EX expire
            is_locked = await client.set(redis_key, "PROCESSING", nx=True, ex=expire)

            if is_locked:
                # 获取锁成功，执行业务逻辑
                try:
                    result = await func(*args, **kwargs)
                    
                    # 将结果序列化并存入 Redis
                    # 使用 jsonable_encoder 处理 Pydantic 模型等
                    serialized_result = jsonable_encoder(result)
                    await client.set(redis_key, json.dumps(serialized_result), ex=expire)
                    
                    return result
                except Exception as e:
                    # 执行失败，删除 Key
                    await client.delete(redis_key)
                    raise e
            else:
                # 锁已存在
                cached_value = await client.get(redis_key)
                
                if cached_value == "PROCESSING":
                    # 正在处理中，返回 409
                    raise HTTPException(status_code=409, detail="Request is processing")
                
                if cached_value:
                    # 已有结果，直接返回
                    return json.loads(cached_value)
                
                # 理论上 key 存在 set nx 才会返回 False，但如果此时 key 过期了，get 会拿到 None
                # 这种情况下，视为新请求，直接执行
                return await func(*args, **kwargs)

        return wrapper
    return decorator
