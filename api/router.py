from fastapi import APIRouter

from api.ai.ai import ai_router
from api.course.comment import comment_router
from api.course.course import course_router
from api.home.home import home_router
from api.order.order import order_router
from api.recommendation.recommendation import recommendation_router
from api.uploader.minio import minio_router
from api.user.user import user_router
from api.ws.ws import ws_router

api_router = APIRouter(prefix='/api')
api_v1_router = APIRouter(prefix='/v1')

api_v1_router.include_router(user_router, tags=["User"])
api_v1_router.include_router(ws_router, tags=["WS"])
api_v1_router.include_router(minio_router, tags=["Minio"])
api_v1_router.include_router(order_router, tags=["Order"])
api_v1_router.include_router(ai_router, tags=["AI"])
api_v1_router.include_router(home_router, tags=["Home"])
api_v1_router.include_router(course_router, tags=["Course"])
api_v1_router.include_router(recommendation_router, tags=["Recommendation"])
api_v1_router.include_router(comment_router, tags=["Course Comment"])
api_router.include_router(api_v1_router)
