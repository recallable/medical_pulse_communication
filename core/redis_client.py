import redis.asyncio as aioredis

from core.config import settings


class RedisClient:
    _pool: aioredis.ConnectionPool = None

    @classmethod
    async def init_pool(cls):
        if not cls._pool:
            cls._pool = aioredis.ConnectionPool.from_url(
                settings.redis_url,
                encoding="utf-8",
                decode_responses=True,
                max_connections=100
            )

    @classmethod
    async def close_pool(cls):
        if cls._pool:
            await cls._pool.disconnect()
            cls._pool = None

    @classmethod
    def get_client(cls) -> aioredis.Redis:
        if not cls._pool:
            raise RuntimeError("Redis pool is not initialized")
        return aioredis.Redis(connection_pool=cls._pool)

redis_client_manager = RedisClient()
