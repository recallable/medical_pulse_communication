from datetime import datetime
from typing import List

from pydantic import BaseModel, Field


class CourseComment(BaseModel):
    """
    MongoDB 课程评价文档模型
    Collection: course_comments
    """
    course_id: int = Field(..., description="课程ID")
    user_id: int = Field(..., description="用户ID")
    # username: str = Field(..., description="用户名 (冗余存储)")
    # user_avatar: Optional[str] = Field(None, description="用户头像 (冗余存储)")
    rating: int = Field(..., ge=1, le=5, description="评分 1-5")
    tags: List[str] = Field(default_factory=list, description="评价标签")
    content: str = Field(..., max_length=300, description="评价内容")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    
    class Config:
        json_schema_extra = {
            "example": {
                "course_id": 101,
                "user_id": 10086,
                "username": "zhangsan",
                "rating": 5,
                "tags": ["干货满满", "通俗易懂"],
                "content": "这门课程非常棒，老师讲得很透彻！",
                "created_at": "2023-10-01T12:00:00"
            }
        }
