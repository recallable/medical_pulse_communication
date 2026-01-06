"""
用户行为日志服务
"""
import logging
from datetime import datetime
from typing import Optional

from fastapi import Request

from models import MedicalCourse
from models.schemas.behavior import UserBehaviorLog, ActionType, UserBehaviorLogRequest
from services.behavior_consumer import publish_behavior_log

logger = logging.getLogger("api")


class UserBehaviorService:
    """用户行为日志服务"""
    
    # 行为类型对应的权重值
    ACTION_WEIGHTS = {
        ActionType.VIEW: 1.0,        # 浏览
        ActionType.FAVORITE: 3.0,    # 收藏
        ActionType.UNFAVORITE: -2.0, # 取消收藏
        ActionType.PURCHASE: 5.0,    # 购买
        ActionType.STUDY: 4.0,       # 学习
        ActionType.RATE: 4.0,        # 评价
    }
    
    async def record_behavior(
        self,
        user_id: int,
        request_data: UserBehaviorLogRequest,
        request: Optional[Request] = None
    ) -> bool:
        """
        记录用户行为
        :param user_id: 用户ID
        :param request_data: 行为请求数据
        :param request: FastAPI请求对象（用于获取IP等信息）
        :return: 是否成功
        """
        try:
            # 获取课程信息
            course = await MedicalCourse.get_or_none(id=request_data.course_id)
            if not course:
                logger.warning(f"课程不存在: {request_data.course_id}")
                return False
            
            # 计算行为权重
            action_value = request_data.action_value
            if action_value is None:
                action_value = self.ACTION_WEIGHTS.get(request_data.action_type, 1.0)
            
            # 构建日志数据
            log_data = UserBehaviorLog(
                user_id=user_id,
                course_id=request_data.course_id,
                action_type=request_data.action_type,
                action_value=action_value,
                course_code=course.course_code,
                course_name=course.course_name,
                medical_department=course.medical_department,
                difficulty_level=course.difficulty_level,
                extra_info=request_data.extra_info or {},
                created_time=datetime.now(),
                ip_address=self._get_client_ip(request) if request else None,
                user_agent=request.headers.get("user-agent") if request else None
            )
            
            # 发布到RabbitMQ
            await publish_behavior_log(log_data.model_dump())
            
            logger.info(f"用户行为已记录: user_id={user_id}, course_id={request_data.course_id}, action={request_data.action_type}")
            return True
            
        except Exception as e:
            logger.error(f"记录用户行为失败: {e}")
            return False
    
    async def record_view(self, user_id: int, course_id: int, request: Optional[Request] = None) -> bool:
        """快捷方法：记录浏览行为"""
        return await self.record_behavior(
            user_id,
            UserBehaviorLogRequest(course_id=course_id, action_type=ActionType.VIEW),
            request
        )
    
    async def record_favorite(self, user_id: int, course_id: int, request: Optional[Request] = None) -> bool:
        """快捷方法：记录收藏行为"""
        return await self.record_behavior(
            user_id,
            UserBehaviorLogRequest(course_id=course_id, action_type=ActionType.FAVORITE),
            request
        )
    
    async def record_purchase(self, user_id: int, course_id: int, request: Optional[Request] = None) -> bool:
        """快捷方法：记录购买行为"""
        return await self.record_behavior(
            user_id,
            UserBehaviorLogRequest(course_id=course_id, action_type=ActionType.PURCHASE),
            request
        )
    
    async def record_study(self, user_id: int, course_id: int, duration: float = None, request: Optional[Request] = None) -> bool:
        """快捷方法：记录学习行为"""
        return await self.record_behavior(
            user_id,
            UserBehaviorLogRequest(
                course_id=course_id, 
                action_type=ActionType.STUDY,
                extra_info={"duration": duration} if duration else {}
            ),
            request
        )
    
    async def record_rate(self, user_id: int, course_id: int, rating: float, request: Optional[Request] = None) -> bool:
        """快捷方法：记录评价行为"""
        return await self.record_behavior(
            user_id,
            UserBehaviorLogRequest(
                course_id=course_id, 
                action_type=ActionType.RATE,
                action_value=rating
            ),
            request
        )
    
    @staticmethod
    def _get_client_ip(request: Request) -> str:
        """获取客户端真实IP"""
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"


user_behavior_service = UserBehaviorService()
