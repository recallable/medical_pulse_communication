from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from services.payment.models import PaymentResult


class PaymentStrategy(ABC):
    """
    抽象支付策略基类
    """
    @abstractmethod
    async def pay(self, order_id: str, amount: float, **kwargs) -> PaymentResult:
        """
        发起支付
        :param order_id: 订单ID
        :param amount: 金额
        :param kwargs: 其他参数
        :return: PaymentResult
        """
        pass

class CallbackHandler(ABC):
    """
    抽象回调处理基类 (接口隔离)
    """
    @abstractmethod
    async def handle_callback(self, data: Dict[str, Any]) -> Optional[str]:
        """
        处理回调通知
        :param data: 回调数据
        :return: 成功返回 order_id，失败返回 None
        """
        pass
