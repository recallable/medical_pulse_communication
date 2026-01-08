from fastapi import APIRouter, Depends, Query

from core.deps import get_current_user_id
from models.schemas.comment import CommentCreate
from services.comment_service import comment_service
from utils.response import APIResponse

comment_router = APIRouter(prefix="/course/comment", tags=["Course Comment"])


@comment_router.post("", summary="发布课程评价")
async def create_comment(
        comment_in: CommentCreate,
        current_user_id: int = Depends(get_current_user_id)
):
    """
    发布课程评价 (需登录)
    """
    result = await comment_service.create_comment(current_user_id, comment_in)
    return APIResponse.success(data=result)


@comment_router.get("/{course_id}", summary="获取课程评价列表")
async def get_comments(
        course_id: int,
        page: int = Query(1, ge=1, description="页码"),
        size: int = Query(10, ge=1, le=100, description="每页数量")
):
    """
    获取课程评价列表 (公开)
    """
    items, total = await comment_service.get_course_comments(course_id, page, size)
    return APIResponse.page(items=items, total=total, page=page, size=size)
