from typing import List, Tuple

from fastapi.encoders import jsonable_encoder

from core.mongodb_client import mongodb_client_manager
from models.document.comment import CourseComment
from models.schemas.comment import CommentCreate, CommentResponse


class CommentService:
    def __init__(self):
        self.collection_name = "course_comments"

    @property
    def collection(self):
        return mongodb_client_manager.get_collection(self.collection_name)

    async def create_comment(self, user_id: int, comment_in: CommentCreate) -> CommentResponse:
        """
        创建评论
        """
        # 构建 MongoDB 文档模型
        comment_doc = CourseComment(
            course_id=comment_in.course_id,
            user_id=user_id,
            # user_avatar=user.avatar, # 假设 User 模型有 avatar 字段，暂时注释
            rating=comment_in.rating,
            tags=comment_in.tags,
            content=comment_in.content
        )

        # 转换为 dict 并写入 MongoDB
        doc_dict = jsonable_encoder(comment_doc)
        result = await self.collection.insert_one(doc_dict)

        # 构造响应
        return CommentResponse(
            id=str(result.inserted_id),
            **comment_doc.dict()
        )

    async def get_course_comments(self, course_id: int, page: int = 1, size: int = 10) -> Tuple[
        List[CommentResponse], int]:
        """
        分页获取课程评论
        """
        skip = (page - 1) * size
        filter_query = {"course_id": course_id}

        # 查询总数
        total = await self.collection.count_documents(filter_query)

        # 查询列表 (按时间倒序)
        cursor = self.collection.find(filter_query).sort("created_at", -1).skip(skip).limit(size)

        comments = []
        async for doc in cursor:
            # 转换 _id 为 id
            doc["id"] = str(doc.pop("_id"))
            comments.append(CommentResponse(**doc))

        return comments, total


comment_service = CommentService()
