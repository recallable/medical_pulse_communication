from datetime import datetime
from decimal import Decimal
from typing import Optional, Any

from pydantic import Field, BaseModel


class MedicalCourseRequest(BaseModel):
    id: Optional[int] = Field(0, description="课程唯一主键")
    course_code: Optional[str] = Field(None, description="课程编码（如：MED-CARDIO-202501）")
    course_name: Optional[str] = Field(None, description="课程名称（如：心内科临床诊疗进阶）")
    medical_department: Optional[str] = Field(None, description="医疗专科（如：心内科、呼吸科、妇产科）")
    limit: Optional[int] = Field(4, description="每页显示数量")
    order_by: Optional[str] = Field(None, description="排序字段")


class MedicalCourseResponse(BaseModel):
    # 核心字段 + Field注释（与数据库字段一一对应）
    id: int = Field(..., description="课程唯一主键")
    course_code: str = Field(..., description="课程编码（如：MED-CARDIO-202501）")
    course_name: str = Field(..., description="课程名称（如：心内科临床诊疗进阶）")
    medical_department: str = Field(..., description="医疗专科（如：心内科、呼吸科、妇产科）")
    applicable_title: Optional[str] = Field(None, description="适用职称/岗位（如：住院医师、主治医师、护士）")
    qualification_req: Optional[str] = Field(None, description="报名资质要求（如：需执业医师证、护士资格证）")
    compliance_record_no: Optional[str] = Field(None, description="医疗课程合规备案编号（行业监管必填）")
    difficulty_level: int = Field(2, description="难度等级（1-入门，2-进阶，3-高阶，4-专家）")
    class_hours: Decimal = Field(0.0, description="课程总课时（如：16.5课时）")
    credit: Optional[Decimal] = Field(0.0, description="继续教育学分（医疗行业特有）")
    price: Decimal = Field(0.00, description="课程售价（元）")
    sale_status: int = Field(1, description="售卖状态（0-下架，1-在售，2-预售）")
    valid_period_days: int = Field(365, description="课程购买后有效期（天，0表示永久有效）")
    refund_rule: Optional[str] = Field(None, description="退款规则（如：开课7天内可退，超过不可退）")
    course_desc: Optional[str] = Field(None, description="课程详细描述")
    status: int = Field(1, description="数据状态（0-禁用，1-启用，2-删除）")
    creator_id: int = Field(..., description="创建人ID（关联用户表）")
    created_time: datetime = Field(..., description="创建时间（带时区）")
    updated_time: datetime = Field(..., description="更新时间（带时区）")
    ext_info: Optional[Any] = Field(None, description="扩展字段（存储临时/个性化信息，如分销比例）")
