from pydantic import BaseModel, Field

class OrderCreate(BaseModel):
    payment_method: str = Field(..., description="支付方式")
    use_grain: bool = Field(..., description="是否使用粮粒")
    course_id: int = Field(..., description="课程ID")
    amount: float = Field(..., description="总金额")

class OrderResponse(BaseModel):
    order_id: str = Field(..., description="订单ID")
    status: str = Field(..., description="状态")
    course_id: int
    amount: float
