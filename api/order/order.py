import uuid

from fastapi import APIRouter, Request, HTTPException

from core.redis_client import redis_client_manager
from models.schemas.order import OrderCreate
from services.payment.factory import PaymentFactory
from utils.idempotency import idempotent
from utils.response import APIResponse

order_router = APIRouter(prefix="/order", tags=["Order"])

@order_router.post("/create")
@idempotent()
async def create_order(request: Request, order_in: OrderCreate):
    """
    创建订单
    Header 中必须包含 Idempotency-Key
    """
    # 模拟业务处理耗时 (例如创建数据库订单记录)
    # await asyncio.sleep(0.5)
    
    order_id = str(uuid.uuid4())
    
    # 1. 简单处理支付方式逻辑
    payment_method = order_in.payment_method
    if order_in.amount == 0:
        payment_method = "free"
    elif order_in.use_grain:
        payment_method = "grain"
    
    try:
        # 2. 获取策略并执行支付
        strategy = PaymentFactory.get_strategy(payment_method)
        payment_result = await strategy.pay(order_id=order_id, amount=order_in.amount)
        
        # 3. 保存订单状态到 Redis (过期时间 24小时)
        redis = redis_client_manager.get_client()
        await redis.set(f"order:{order_id}", payment_result.status, ex=86400)
        
        # 3. 构造返回数据
        data = {
            "user_id": request.state.user_id if hasattr(request.state, "user_id") else None,
            "order_id": order_id,
            "status": payment_result.status,
            "course_id": order_in.course_id,
            "amount": order_in.amount,
            "payment_info": payment_result.dict(exclude_none=True)
        }
        
        return APIResponse.success(data=data)
        
    except ValueError as e:
        return APIResponse.error(message=str(e), code=400)
    except Exception as e:
        return APIResponse.error(message=f"订单创建失败: {str(e)}", code=500)


@order_router.post("/notify/{payment_method}")
async def notify_callback(payment_method: str, request: Request):
    """
    统一回调接口
    """
    try:
        # 1. 获取回调处理器
        handler = PaymentFactory.get_callback_handler(payment_method)
        
        # 2. 解析回调数据 (这里假设是 Form 表单或 JSON)
        # 根据不同渠道可能不同，简单起见取 json 或 form
        if request.headers.get("content-type") == "application/json":
            data = await request.json()
        else:
            form = await request.form()
            data = dict(form)
            
        # 3. 处理回调
        order_id = await handler.handle_callback(data)
        
        if order_id:
            # 4. 更新 Redis 中的订单状态
            redis = redis_client_manager.get_client()
            await redis.set(f"order:{order_id}", "COMPLETED", ex=86400)
            
            return "success" # 支付宝等通常要求返回 success 字符串
        else:
            return "fail"
            
    except ValueError as e:
        # 不支持回调的策略
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@order_router.get("/{order_id}")
async def get_order_status(order_id: str):
    """
    查询订单状态 (用于前端轮询)
    """
    redis = redis_client_manager.get_client()
    status = await redis.get(f"order:{order_id}")
    
    if not status:
        return APIResponse.error(message="订单不存在或已过期", code=404)
        
    return APIResponse.success(data={"order_id": order_id, "status": status})
