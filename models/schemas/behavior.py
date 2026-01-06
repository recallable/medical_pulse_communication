"""
用户行为日志模型（MongoDB Document）
"""
from datetime import datetime
from enum import Enum
from typing import Optional, Any

from pydantic import BaseModel, Field


class ActionType(str, Enum):
    """用户行为类型枚举"""
    VIEW = "view"           # 浏览课程
    FAVORITE = "favorite"   # 收藏课程
    UNFAVORITE = "unfavorite"  # 取消收藏
    PURCHASE = "purchase"   # 购买课程
    STUDY = "study"         # 学习课程
    RATE = "rate"           # 评价课程


class UserBehaviorLog(BaseModel):
    """用户行为日志文档模型"""
    user_id: int = Field(..., description="用户ID")
    course_id: int = Field(..., description="课程ID")
    action_type: ActionType = Field(..., description="行为类型")
    action_value: Optional[float] = Field(None, description="行为权重值（如评分分数、学习时长等）")
    course_code: Optional[str] = Field(None, description="课程编码")
    course_name: Optional[str] = Field(None, description="课程名称")
    medical_department: Optional[str] = Field(None, description="医疗科室")
    difficulty_level: Optional[int] = Field(None, description="课程难度等级")
    extra_info: Optional[dict[str, Any]] = Field(default_factory=dict, description="扩展信息")
    created_time: datetime = Field(default_factory=datetime.now, description="行为发生时间")
    ip_address: Optional[str] = Field(None, description="用户IP地址")
    user_agent: Optional[str] = Field(None, description="用户代理")
    
    class Config:
        use_enum_values = True


class UserBehaviorLogRequest(BaseModel):
    """用户行为日志请求模型"""
    course_id: int = Field(..., description="课程ID")
    action_type: ActionType = Field(..., description="行为类型")
    action_value: Optional[float] = Field(None, description="行为权重值")
    extra_info: Optional[dict[str, Any]] = Field(default_factory=dict, description="扩展信息")


class UserBehaviorLogResponse(BaseModel):
    """用户行为日志响应模型"""
    id: str = Field(..., description="日志ID")
    user_id: int = Field(..., description="用户ID")
    course_id: int = Field(..., description="课程ID")
    action_type: str = Field(..., description="行为类型")
    action_value: Optional[float] = Field(None, description="行为权重值")
    course_name: Optional[str] = Field(None, description="课程名称")
    created_time: datetime = Field(..., description="行为发生时间")
