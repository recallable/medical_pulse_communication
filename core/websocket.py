# core/websocket.py
from typing import Dict

from fastapi import WebSocket


class ConnectionManager:
    def __init__(self):
        # 🔴 关键修改：从 List 改为 Dict，key 是 client_id，value 是 WebSocket 对象
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        # 建立连接
        await websocket.accept()
        # 记录：将 client_id 和 websocket 绑定
        self.active_connections[str(client_id)] = websocket

    def disconnect(self, client_id: str):
        # 移除连接
        client_id = str(client_id)
        if client_id in self.active_connections:
            del self.active_connections[client_id]

    async def send_personal_message(self, message: str, websocket: WebSocket):
        # 直接给某个 socket 发消息 (保持原有逻辑)
        await websocket.send_text(message)

    async def send_to_user(self, client_id: str, message: str):
        # ✅ 新增功能：通过 ID 给指定用户发消息
        client_id = str(client_id)
        websocket = self.active_connections.get(client_id)
        if websocket:
            await websocket.send_text(message)
            return True
        return False

    async def broadcast(self, message: str):
        # 广播：遍历字典的所有 value
        for connection in self.active_connections.values():
            try:
                await connection.send_text(message)
            except Exception:
                pass


manager = ConnectionManager()
