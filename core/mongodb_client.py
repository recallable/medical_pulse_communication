"""
MongoDB异步客户端管理
"""
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from core.config import settings


class MongoDBClientManager:
    """MongoDB连接管理器"""
    
    def __init__(self):
        self._client: AsyncIOMotorClient | None = None
        self._db: AsyncIOMotorDatabase | None = None
    
    async def init_client(self):
        """初始化MongoDB客户端"""
        self._client = AsyncIOMotorClient(settings.mongodb_url)
        self._db = self._client[settings.mongodb_database]
        # 创建索引
        await self._create_indexes()
    
    async def _create_indexes(self):
        """创建必要的索引"""
        # 用户行为日志集合索引
        user_behavior_collection = self._db["user_behavior_log"]
        await user_behavior_collection.create_index("user_id")
        await user_behavior_collection.create_index("course_id")
        await user_behavior_collection.create_index("action_type")
        await user_behavior_collection.create_index("created_time")
        await user_behavior_collection.create_index([("user_id", 1), ("course_id", 1)])
        
        # 课程评价集合索引
        course_comment_collection = self._db["course_comments"]
        await course_comment_collection.create_index("course_id")
        await course_comment_collection.create_index("created_at")
        await course_comment_collection.create_index([("course_id", 1), ("created_at", -1)])
    
    async def close_client(self):
        """关闭MongoDB客户端"""
        if self._client:
            self._client.close()
            self._client = None
            self._db = None
    
    @property
    def client(self) -> AsyncIOMotorClient:
        """获取MongoDB客户端"""
        if self._client is None:
            raise RuntimeError("MongoDB client not initialized")
        return self._client
    
    @property
    def db(self) -> AsyncIOMotorDatabase:
        """获取数据库实例"""
        if self._db is None:
            raise RuntimeError("MongoDB database not initialized")
        return self._db
    
    def get_collection(self, name: str):
        """获取集合"""
        return self.db[name]


mongodb_client_manager = MongoDBClientManager()
