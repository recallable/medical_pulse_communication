import json

from fastapi import APIRouter, Depends
from starlette.websockets import WebSocket, WebSocketDisconnect

from core.deps import validate_ws_token
from core.websocket import manager

ws_router = APIRouter(prefix='/ws')


@ws_router.websocket("/{client_id}")
async def websocket_endpoint(
        websocket: WebSocket,
        client_id: int,
        user_id: str = Depends(validate_ws_token)
):
    """
    WebSocket 连接点
    :param websocket: WebSocket 连接对象
    :param client_id: 客户端 ID
    :param user_id: 用户 ID
    :return: 无
    """
    # 如果 validate_ws_token 里执行了 close，这里 user_id 会是 None
    # 必须判断一下，直接返回，停止执行后续逻辑
    if user_id is None:
        return

        # ✅ 修改点：传入 client_id
    await manager.connect(websocket, str(client_id))

    try:
        while True:
            data = await websocket.receive_text()
            await manager.send_personal_message(f"你发送了: {data}", websocket)
            data = json.loads(data)
            to_user_id = data.get('to')
            content = data.get('content')
            await manager.send_to_user(to_user_id, json.dumps({"to": to_user_id, "content": content}))

    except WebSocketDisconnect:
        # ✅ 修改点：传入 client_id 用于移除
        manager.disconnect(str(client_id))
        await manager.broadcast(f"用户 #{client_id} 离开了聊天室")
