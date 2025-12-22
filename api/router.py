from fastapi import APIRouter

from api.user.user import user_router

api_router = APIRouter(prefix='/api')
api_v1_router = APIRouter(prefix='/v1')

api_v1_router.include_router(user_router, tags=["User"])
api_router.include_router(api_v1_router)
