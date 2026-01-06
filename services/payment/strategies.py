from typing import Dict, Any, Optional

from tortoise import timezone

from models.entity.order import Order
from services.payment.interfaces import PaymentStrategy, CallbackHandler
from services.payment.models import PaymentResult
from utils.alipay import AliPaySDK


class FreeStrategy(PaymentStrategy):
    """
    0元购/麦粒支付策略
    """

    async def pay(self, order_id: str, amount: float, **kwargs) -> PaymentResult:
        # 0元购或积分兑换，直接成功
        return PaymentResult(
            is_instant_success=True,
            status="COMPLETED",
            message="支付成功"
        )


class AlipayStrategy(PaymentStrategy, CallbackHandler):
    """
    支付宝支付策略
    """

    async def pay(self, order_id: str, amount: float, **kwargs) -> PaymentResult:
        # 模拟生成支付宝支付链接
        fake_url = AliPaySDK().page_pay(order_id, amount, "订单标题")
        # fake_url = f"https://openapi.alipay.com/gateway.do?order_id={order_id}&amt={amount}"
        try:
            await Order.create(order_no=order_id, user_id=kwargs.get('user_id'),
                               course_id=kwargs.get('course_id'), original_price=amount,
                               real_price=amount, payment_method="ALIPAY", status="PENDING_PAYMENT", )
        except Exception as e:
            raise ValueError(f"创建订单失败: {str(e)}")
        return PaymentResult(
            is_instant_success=False,
            status="PENDING",
            payment_url=fake_url,
            message="请前往支付宝完成支付"
        )

    async def handle_callback(self, data: Dict[str, Any]) -> Optional[str]:
        # 处理支付宝回调逻辑
        # 验证签名、检查金额等...
        # 支付宝回调参数
        print(f"支付宝回调参数：{data}")
        alipay_sdk = AliPaySDK()
        verify_result = alipay_sdk.check_sign(data)
        print(f"验证结果：{verify_result}")
        if not verify_result:
            raise ValueError("支付宝签名验证失败")

        # 3. 处理支付结果
        out_trade_no = data.get('out_trade_no')  # 商户订单号（即订单ID）
        trade_status = data.get('trade_status')  # 支付状态
        trade_no = data.get('trade_no')  # 支付状态
        if trade_status == 'TRADE_SUCCESS':
            order = await Order.filter(order_no=out_trade_no,
                                       status="PENDING_PAYMENT",  # 待支付状态
                                       is_deleted=0).first()
            # 更新订单状态

            await Order.filter(id=order.id, order_no=order.order_no) \
                .update(status="COMPLETED", paid_at=timezone.now(),
                        transaction_id=trade_no)
            return out_trade_no

        return None


class WechatPayStrategy(PaymentStrategy, CallbackHandler):
    """
    微信支付策略
    """

    async def pay(self, order_id: str, amount: float, **kwargs) -> PaymentResult:
        # 模拟生成微信支付二维码链接 (Code URL)
        fake_url = f"weixin://wxpay/bizpayurl?pr={order_id}&amt={amount}"

        return PaymentResult(
            is_instant_success=False,
            status="PENDING",
            payment_url=fake_url,
            message="请使用微信扫描二维码完成支付"
        )

    async def handle_callback(self, data: Dict[str, Any]) -> Optional[str]:
        # 处理微信支付回调逻辑
        # 微信通常返回 XML，这里假设上层已经解析为 Dict
        print(f"WechatPay callback received: {data}")

        # 微信支付成功状态通常是 result_code 和 return_code 都为 SUCCESS
        if data.get("result_code") == "SUCCESS":
            # 假设回调数据中包含 order_id
            return data.get("order_id")
        return None
