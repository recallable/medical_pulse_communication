from datetime import datetime
from typing import List

from pydantic import BaseModel, Field


class CommentCreate(BaseModel):
    course_id: int = Field(..., description="课程ID")
    rating: int = Field(..., ge=1, le=5, description="评分 1-5")
    tags: List[str] = Field(default_factory=list, description="标签列表")
    content: str = Field(..., max_length=300, description="评价内容 (限300字)")

class CommentResponse(BaseModel):
    id: str = Field(..., description="评论ID")
    course_id: int
    user_id: int
    # username: Optional[str]
    # user_avatar: Optional[str]
    rating: int
    tags: List[str]
    content: str
    created_at: datetime
