from typing import List, Optional, Any, Dict

from pydantic import BaseModel, Field


# --- 请求模型 ---
class SearchFilters(BaseModel):
    department: Optional[str] = Field(None, description="科室筛选")
    doctor_name: Optional[str] = Field(None, description="医生筛选")
    min_age: Optional[int] = Field(None, description="最小年龄")
    max_age: Optional[int] = Field(None, description="最大年龄")
    # 允许接收任意额外的扩展字段筛选，例如 {"extend_key": "检查指标", "extend_value": "高"}
    extend_key: Optional[str] = None
    extend_value: Optional[str] = None

class SearchRequest(BaseModel):
    keyword: Optional[str] = Field(None, description="搜索关键词", example="高血压 头痛")
    page: int = Field(1, ge=1, description="页码")
    size: int = Field(10, ge=1, le=100, description="每页条数")
    filters: Optional[SearchFilters] = None

# --- 响应模型 ---
class MedicalRecordDTO(BaseModel):
    id: Optional[int]
    record_no: Optional[str]
    patient_name: Optional[str]
    age: Optional[int]
    department: Optional[str]
    score: float
    # 高亮字段（可能为空，如果没搜到关键词）
    highlight_disease: Optional[str]
    highlight_symptoms: Optional[str]
    # 原始完整数据
    raw_data: Dict[str, Any]

class SearchResponse(BaseModel):
    total: int
    took_ms: int
    data: List[MedicalRecordDTO]