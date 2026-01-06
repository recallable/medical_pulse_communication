from typing import Optional

from pydantic import BaseModel, Field


class PaymentResult(BaseModel):
    is_instant_success: bool = Field(..., description="是否立即支付成功")
    status: str = Field(..., description="支付状态: PENDING, COMPLETED, FAILED")
    payment_url: Optional[str] = Field(None, description="第三方支付链接 (如支付宝/微信)")
    transaction_id: Optional[str] = Field(None, description="交易流水号")
    message: Optional[str] = Field(None, description="提示信息")
