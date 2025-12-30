import json
import time
import uuid

from fastapi import APIRouter, Depends
from starlette.responses import StreamingResponse

from core.deps import get_current_user_id
from middleware.exception import BusinessException
from models.schemas.ai import AiRequest
from services.ai import ai_service
from utils.response import APIResponse

ai_router = APIRouter(prefix='/ai')


@ai_router.post('/chat')
async def chat(
        request: AiRequest,
        user_id: int = Depends(get_current_user_id),
):
    """
    AI 聊天接口
    """

    if not user_id:
        raise BusinessException(message="用户未登录", code=401)
    generator = ai_service.chat(user_id, request.question, request.session_id)
    return StreamingResponse(generator, media_type='text/event-stream')


@ai_router.post('/chat/create-session')
async def create_session(
        user_id: int = Depends(get_current_user_id),
):
    """
    AI 创建会话接口
    """

    if not user_id:
        raise BusinessException(message="用户未登录", code=401)
    from core.redis_client import redis_client_manager as redis

    redis = redis.get_client()

    session_id = str(uuid.uuid4())

    chat_message_hash_key = f'chat:message:hash:{user_id}:{session_id}'
    chat_message_set_key = f'chat:message:set:{user_id}'

    await redis.hset(chat_message_hash_key, mapping={
        'last_message': '',
        'created_time': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()),
        'session_id': session_id
    })
    await redis.sadd(chat_message_set_key, session_id)

    return APIResponse.success(data={
        'session_id': session_id
    })


@ai_router.get('/chat/session-list')
async def session_list(
        user_id: int = Depends(get_current_user_id),
):
    """
    AI 会话列表接口
    """
    if not user_id:
        raise BusinessException(message="用户未登录", code=401)
    from core.redis_client import redis_client_manager as redis

    redis = redis.get_client()

    chat_message_set_key = f'chat:message:set:{user_id}'
    # # 根据用户的id查找到所有的session_id
    session_ids = await redis.smembers(chat_message_set_key)
    session_ids = [session_id for session_id in session_ids]

    # 根据session_id查询会话信息
    session_info = []
    for session_id in session_ids:
        session_info.append(await redis.hgetall(f'chat:message:hash:{user_id}:{session_id}'))

    session_info.sort(key=lambda x: x['created_time'], reverse=True)

    return APIResponse.success(data=session_info)


@ai_router.get('/chat/session-message')
async def session_message(
        session_id: str,
        user_id: int = Depends(get_current_user_id),
):
    from core.redis_client import redis_client_manager as redis

    redis = redis.get_client()
    session_list_key = f'chat:message:list:{user_id}:{session_id}'
    messages = []
    for data in await redis.lrange(session_list_key, 0, -1):
        messages.append(json.loads(data))
    return APIResponse.success(data=messages)
