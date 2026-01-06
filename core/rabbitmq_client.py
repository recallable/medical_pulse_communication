"""
RabbitMQ异步客户端管理
"""
import asyncio
import json
from typing import Callable, Any

from aio_pika import connect_robust, Message, DeliveryMode
from aio_pika.abc import AbstractRobustConnection, AbstractChannel, AbstractQueue

from core.config import settings


class RabbitMQClientManager:
    """RabbitMQ连接管理器"""
    
    # 队列名称常量
    USER_BEHAVIOR_LOG_QUEUE = "user_behavior_log_queue"
    
    def __init__(self):
        self._connection: AbstractRobustConnection | None = None
        self._channel: AbstractChannel | None = None
        self._queues: dict[str, AbstractQueue] = {}
        self._consumer_task: asyncio.Task | None = None
    
    async def init_connection(self):
        """初始化RabbitMQ连接"""
        self._connection = await connect_robust(settings.rabbitmq_url)
        self._channel = await self._connection.channel()
        # 声明队列
        await self._declare_queues()
    
    async def _declare_queues(self):
        """声明所需队列"""
        # 用户行为日志队列
        queue = await self._channel.declare_queue(
            self.USER_BEHAVIOR_LOG_QUEUE,
            durable=True  # 持久化队列
        )
        self._queues[self.USER_BEHAVIOR_LOG_QUEUE] = queue
    
    async def close_connection(self):
        """关闭RabbitMQ连接"""
        if self._consumer_task:
            self._consumer_task.cancel()
            try:
                await self._consumer_task
            except asyncio.CancelledError:
                pass
        if self._connection:
            await self._connection.close()
            self._connection = None
            self._channel = None
            self._queues = {}
    
    @property
    def channel(self) -> AbstractChannel:
        """获取通道"""
        if self._channel is None:
            raise RuntimeError("RabbitMQ channel not initialized")
        return self._channel
    
    async def publish_message(self, queue_name: str, message_body: dict):
        """
        发布消息到队列
        :param queue_name: 队列名称
        :param message_body: 消息体（字典）
        """
        message = Message(
            body=json.dumps(message_body, ensure_ascii=False, default=str).encode(),
            delivery_mode=DeliveryMode.PERSISTENT  # 消息持久化
        )
        await self._channel.default_exchange.publish(
            message,
            routing_key=queue_name
        )
    
    async def start_consumer(self, queue_name: str, callback: Callable[[dict], Any]):
        """
        启动消费者
        :param queue_name: 队列名称
        :param callback: 消息处理回调函数
        """
        queue = self._queues.get(queue_name)
        if not queue:
            raise ValueError(f"Queue {queue_name} not found")
        
        async def process_message(message):
            async with message.process():
                body = json.loads(message.body.decode())
                await callback(body)
        
        self._consumer_task = asyncio.create_task(self._consume(queue, process_message))
    
    async def _consume(self, queue: AbstractQueue, callback: Callable):
        """持续消费消息"""
        async with queue.iterator() as queue_iter:
            async for message in queue_iter:
                await callback(message)


rabbitmq_client_manager = RabbitMQClientManager()
