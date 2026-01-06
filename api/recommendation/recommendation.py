"""
推荐系统API路由
"""
from fastapi import APIRouter, Request, Depends

from core.deps import get_current_user
from models.schemas.behavior import UserBehaviorLogRequest
from models.schemas.recommendation import RecommendationRequest, RecommendationResponse, RecommendationItem
from services.behavior_service import user_behavior_service
from services.recommendation import item_cf_recommender
from utils.response import APIResponse

recommendation_router = APIRouter(prefix='/recommendation')


@recommendation_router.post('/record-behavior')
async def record_behavior(
    request_data: UserBehaviorLogRequest,
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """
    记录用户行为
    
    行为类型:
    - view: 浏览课程
    - favorite: 收藏课程
    - unfavorite: 取消收藏
    - purchase: 购买课程
    - study: 学习课程
    - rate: 评价课程
    """
    user_id = current_user.get("user_id")
    success = await user_behavior_service.record_behavior(
        user_id=user_id,
        request_data=request_data,
        request=request
    )
    
    if success:
        return APIResponse.success(message="行为记录成功")
    return APIResponse.error(message="行为记录失败")


@recommendation_router.post('/course-recommend')
async def get_course_recommendations(
    request_data: RecommendationRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    获取课程推荐列表
    
    基于物品的协同过滤算法，混合用户行为和课程属性相似度
    """
    user_id = current_user.get("user_id")
    
    recommendations = await item_cf_recommender.get_recommendations(
        user_id=user_id,
        top_n=request_data.top_n,
        exclude_interacted=request_data.exclude_interacted
    )
    
    response = RecommendationResponse(
        user_id=user_id,
        total=len(recommendations),
        recommendations=[RecommendationItem(**r) for r in recommendations]
    )
    
    return APIResponse.success(data=response.model_dump())


@recommendation_router.post('/view/{course_id}')
async def record_view_behavior(
    course_id: int,
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """快捷接口：记录浏览行为"""
    user_id = current_user.get("user_id")
    success = await user_behavior_service.record_view(user_id, course_id, request)
    
    if success:
        return APIResponse.success(message="浏览记录成功")
    return APIResponse.error(message="记录失败")


@recommendation_router.post('/favorite/{course_id}')
async def record_favorite_behavior(
    course_id: int,
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """快捷接口：记录收藏行为"""
    user_id = current_user.get("user_id")
    success = await user_behavior_service.record_favorite(user_id, course_id, request)
    
    if success:
        return APIResponse.success(message="收藏记录成功")
    return APIResponse.error(message="记录失败")


@recommendation_router.post('/purchase/{course_id}')
async def record_purchase_behavior(
    course_id: int,
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """快捷接口：记录购买行为"""
    user_id = current_user.get("user_id")
    success = await user_behavior_service.record_purchase(user_id, course_id, request)
    
    if success:
        return APIResponse.success(message="购买记录成功")
    return APIResponse.error(message="记录失败")


@recommendation_router.post('/hot-courses')
async def get_hot_courses(top_n: int = 10):
    """
    获取热门课程（不需要登录）
    用于首页展示或新用户推荐
    """
    hot_courses = await item_cf_recommender._get_hot_courses(top_n)
    
    return APIResponse.success(data={
        "total": len(hot_courses),
        "courses": hot_courses
    })
