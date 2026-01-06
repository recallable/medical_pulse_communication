from pydantic import BaseModel, Field

class OrderCreate(BaseModel):
    product_id: int = Field(..., description="商品ID")
    count: int = Field(..., description="数量")
    amount: float = Field(..., description="总金额")

class OrderResponse(BaseModel):
    order_id: str = Field(..., description="订单ID")
    status: str = Field(..., description="状态")
    product_id: int
    amount: float
