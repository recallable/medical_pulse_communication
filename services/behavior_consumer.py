"""
用户行为日志消费者 - 从RabbitMQ消费消息并写入MongoDB
"""
import logging
from datetime import datetime

from core.mongodb_client import mongodb_client_manager
from core.rabbitmq_client import rabbitmq_client_manager, RabbitMQClientManager

logger = logging.getLogger("api")

# MongoDB集合名称
USER_BEHAVIOR_COLLECTION = "user_behavior_log"


async def process_behavior_log(message: dict):
    """
    处理用户行为日志消息
    :param message: 消息体
    """
    try:
        # 添加写入时间
        message["inserted_time"] = datetime.now()
        
        # 写入MongoDB
        collection = mongodb_client_manager.get_collection(USER_BEHAVIOR_COLLECTION)
        result = await collection.insert_one(message)
        
        logger.info(f"用户行为日志已写入MongoDB: {result.inserted_id}")
    except Exception as e:
        logger.error(f"写入用户行为日志失败: {e}")
        raise


async def start_behavior_log_consumer():
    """启动用户行为日志消费者"""
    try:
        await rabbitmq_client_manager.start_consumer(
            RabbitMQClientManager.USER_BEHAVIOR_LOG_QUEUE,
            process_behavior_log
        )
        logger.info("用户行为日志消费者已启动")
    except Exception as e:
        logger.error(f"启动用户行为日志消费者失败: {e}")
        raise


async def publish_behavior_log(log_data: dict):
    """
    发布用户行为日志到RabbitMQ
    :param log_data: 日志数据
    """
    try:
        await rabbitmq_client_manager.publish_message(
            RabbitMQClientManager.USER_BEHAVIOR_LOG_QUEUE,
            log_data
        )
        logger.debug(f"用户行为日志已发布到队列: user_id={log_data.get('user_id')}, action={log_data.get('action_type')}")
    except Exception as e:
        logger.error(f"发布用户行为日志失败: {e}")
        raise
