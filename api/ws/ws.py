from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
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
            # await manager.broadcast(f"用户 #{client_id} 说: {data}")

    except WebSocketDisconnect:
        # ✅ 修改点：传入 client_id 用于移除
        manager.disconnect(str(client_id))
        await manager.broadcast(f"用户 #{client_id} 离开了聊天室")


# 定义请求体模型
class MessageSchema(BaseModel):
    message: str


@ws_router.post("/send/{client_id}")
async def send_message_to_client(client_id: str, msg: MessageSchema):
    """
    HTTP 接口：给指定 client_id 推送消息
    """
    # 调用管理器的 send_to_user 方法
    success = await manager.send_to_user(client_id, msg.message)

    if not success:
        # 如果用户不在线（不在 active_connections 里）
        raise HTTPException(status_code=404, detail="User not connected")

    return {"message": "Message sent", "client_id": client_id}
