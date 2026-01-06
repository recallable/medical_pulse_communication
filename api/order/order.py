import asyncio
import uuid

from fastapi import APIRouter, Request

from models.schemas.order import OrderCreate
from utils.idempotency import idempotent
from utils.response import APIResponse

order_router = APIRouter(prefix="/order", tags=["Order"])

@order_router.post("/create")
@idempotent()
async def create_order(request: Request, order_in: OrderCreate):
    """
    创建订单 (幂等性演示)
    Header 中必须包含 Idempotency-Key
    """
    # 模拟业务处理耗时
    await asyncio.sleep(2)
    
    order_id = str(uuid.uuid4())
    
    data = {
        "user_id": request.state.user_id,
        "order_id": order_id,
        "status": "created",
        "course_id": order_in.course_id,
        "amount": order_in.amount
    }
    
    return APIResponse.success(data=data)
