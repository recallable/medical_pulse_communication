import asyncio
import json
import logging
import random

from fastapi import APIRouter, HTTPException

from core.redis_client import redis_client_manager
from models.entity.article import Article
from models.schemas.article import ArticleResponse, ArticleRequest
from utils.response import APIResponse

home_router = APIRouter(prefix="/home")
logger = logging.getLogger("api")


@home_router.post('/article-list')
async def article_list(article_request: ArticleRequest):
    redis = redis_client_manager.get_client()
    cache_key = f"article_list_{article_request.article_id}"
    lock_key = f"article_list_lock_{article_request.article_id}"

    # --- 1. 快速路径：直接查缓存 ---
    redis_articles = await redis.lrange(cache_key, 0, -1)
    if redis_articles:
        return APIResponse.success(data=[json.loads(article) for article in redis_articles])

    # 定义一个锁对象
    # blocking=False 表示非阻塞：抢不到锁立刻返回 False，而不是在原地等
    lock = redis.lock(lock_key, blocking_timeout=0, timeout=10)

    # 尝试获取锁
    have_lock = await lock.acquire(blocking=False)

    if have_lock:
        # ==========================================
        # 👑 这里的代码，100个请求里只有 1 个会执行
        # ==========================================
        try:
            # Double Check (防止在抢锁的瞬间，别人已经写好了)
            redis_articles = await redis.lrange(cache_key, 0, -1)
            if redis_articles:
                return APIResponse.success(data=[json.loads(article) for article in redis_articles])

            # 查数据库
            logger.info("👑 获得锁，正在查询数据库... ID: %s", article_request.article_id)
            articles = await Article \
                .filter(id__gt=article_request.article_id).all() \
                .limit(article_request.limit) \
                .order_by('id')

            response_data = [
                ArticleResponse(
                    id=article.id,
                    title=article.title,
                    content=article.content,
                    description=article.description,
                    comment_count=article.comment_count,
                    type=article.type,
                    url=article.url,
                    thumb=article.thumb,
                    input_time=article.input_time.strftime("%Y-%m-%d %H:%M:%S") if article.input_time else None
                )
                for article in articles
            ]

            # 写缓存
            if response_data:
                json_list = [json.dumps(article.model_dump()) for article in response_data]
                async with redis.pipeline(transaction=True) as pipe:
                    await pipe.delete(cache_key)
                    await pipe.rpush(cache_key, *json_list)
                    await pipe.expire(cache_key, 300)
                    await pipe.execute()

            return APIResponse.success(data=response_data)

        finally:
            # 无论如何要释放锁，不然别人会死等
            await lock.release()

    else:
        # ==========================================
        # 🧘 这里的代码，其余 99 个请求会执行 (自旋等待)
        # ==========================================
        logger.info("🧘 没抢到锁，正在等待缓存生成...")

        # 设置最大等待次数，防止死循环 (比如等 5秒: 50 * 0.1s)
        for _ in range(50):
            # 1. 睡一小会儿 (给 Leader 一点时间查库)
            # 使用 random 防止所有线程同时唤醒冲击 Redis (雷惊群效应)
            await asyncio.sleep(random.uniform(0.1, 0.2))

            # 2. 醒来去看看缓存有没有了
            redis_articles = await redis.lrange(cache_key, 0, -1)
            if redis_articles:
                logger.info("✅ 等到了！从缓存返回")
                return APIResponse.success(data=[json.loads(article) for article in redis_articles])

        # 3. 如果等了 5 秒还没数据，说明 Leader 挂了或者数据库卡死了
        # 抛出异常或者返回空，坚决不查库
        raise HTTPException(status_code=503, detail="Server busy, please try again later")
