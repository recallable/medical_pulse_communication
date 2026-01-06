from typing import Dict, Type

from services.payment.interfaces import PaymentStrategy, CallbackHandler
from services.payment.strategies import FreeStrategy, AlipayStrategy, WechatPayStrategy


class PaymentFactory:
    """
    支付策略工厂
    """
    _strategies: Dict[str, Type[PaymentStrategy]] = {
        "free": FreeStrategy,
        "grain": FreeStrategy, # 麦粒支付复用 FreeStrategy
        "alipay": AlipayStrategy,
        "wechat": WechatPayStrategy
    }

    @classmethod
    def get_strategy(cls, payment_method: str) -> PaymentStrategy:
        strategy_cls = cls._strategies.get(payment_method)
        if not strategy_cls:
            raise ValueError(f"不支持的支付方式: {payment_method}")
        return strategy_cls()

    @classmethod
    def get_callback_handler(cls, payment_method: str) -> CallbackHandler:
        strategy = cls.get_strategy(payment_method)
        if not isinstance(strategy, CallbackHandler):
            raise ValueError(f"支付方式 {payment_method} 不支持回调处理")
        return strategy
