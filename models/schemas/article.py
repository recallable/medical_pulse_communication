from typing import Optional

from pydantic import BaseModel, Field


class ArticleRequest(BaseModel):
    article_id: int = Field(0, description="文章ID")
    limit: int = Field(10, description="每页数量")


class ArticleResponse(BaseModel):
    """文章信息"""
    id: int = Field(..., description="文章ID")
    title: Optional[str] = Field(None, description="文章标题")
    content: Optional[str] = Field(None, description="文章内容")
    description: Optional[str] = Field(None, description="文章描述")
    comment_count: Optional[int] = Field(None, description="文章评论数")
    type: Optional[str] = Field(None, description="文章类型")
    url: Optional[str] = Field(None, description="文章URL")
    thumb: Optional[str] = Field(None, description="文章缩略图")
    input_time: Optional[str] = Field(None, description="文章发布时间")

    def dict(self, *args, **kwargs):
        """
        重写dict方法, 将input_time转换为字符串
        """
        data = super().model_dump(*args, **kwargs)
        if data.get("input_time"):
            data["input_time"] = data["input_time"].strftime("%Y-%m-%d %H:%M:%S")
        return data