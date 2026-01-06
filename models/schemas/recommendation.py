"""
推荐系统API
"""
from pydantic import BaseModel, Field


class RecommendationRequest(BaseModel):
    """推荐请求"""
    top_n: int = Field(10, ge=1, le=50, description="推荐数量")
    exclude_interacted: bool = Field(True, description="是否排除已交互课程")


class RecommendationItem(BaseModel):
    """推荐项"""
    course_id: int = Field(..., description="课程ID")
    course_code: str = Field(..., description="课程编码")
    course_name: str = Field(..., description="课程名称")
    medical_department: str = Field(..., description="医疗科室")
    difficulty_level: int = Field(..., description="难度等级")
    price: float = Field(..., description="课程价格")
    recommendation_score: float = Field(..., description="推荐分数")
    recommendation_reason: str = Field(..., description="推荐理由")


class RecommendationResponse(BaseModel):
    """推荐响应"""
    user_id: int = Field(..., description="用户ID")
    total: int = Field(..., description="推荐总数")
    recommendations: list[RecommendationItem] = Field(default_factory=list, description="推荐列表")
