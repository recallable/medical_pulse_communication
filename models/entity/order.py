from enum import Enum

from tortoise import fields, models


# 1. 定义枚举，对应 SQL 中的 status 和 payment_method
class OrderStatus(str, Enum):
    PENDING_PAYMENT = "PENDING_PAYMENT"  # 待支付
    COMPLETED = "COMPLETED"  # 已完成
    CANCELLED = "CANCELLED"  # 已取消
    REFUNDED = "REFUNDED"  # 已退款


class PaymentMethod(str, Enum):
    ALIPAY = "ALIPAY"
    WECHAT = "WECHAT"
    WHEAT = "WHEAT"
    FREE = "FREE"


class Order(models.Model):
    """
    课程购买订单表
    """
    # 主键 (BIGSERIAL)
    id = fields.BigIntField(pk=True, description="主键ID")

    # 业务订单号 (UUID)
    order_no = fields.CharField(max_length=64, unique=True, description="业务订单号(UUID)")

    # 关联信息 (这里使用 BigIntField，如果你有 User/Course 模型，建议换成 ForeignKeyField)
    # user = fields.ForeignKeyField('models.User', related_name='orders', description="购买用户")
    user_id = fields.BigIntField(index=True, description="购买用户 ID")

    # course = fields.ForeignKeyField('models.Course', related_name='orders', description="购买课程")
    course_id = fields.BigIntField(description="购买课程 ID")

    # 金额信息 (DECIMAL)
    # Tortoise 会自动映射为 Python 的 Decimal 对象
    original_price = fields.DecimalField(max_digits=10, decimal_places=2, default=0.00, description="原价")
    real_price = fields.DecimalField(max_digits=10, decimal_places=2, default=0.00, description="实际支付金额")

    # 支付相关
    # 使用 null=True 对应 SQL 的 DEFAULT NULL
    payment_method = fields.CharEnumField(
        PaymentMethod,
        max_length=32,
        null=True,
        description="支付方式"
    )

    transaction_id = fields.CharField(
        max_length=128,
        null=True,
        index=True,
        description="第三方支付流水号"
    )

    # 状态机
    status = fields.CharEnumField(
        OrderStatus,
        max_length=32,
        default=OrderStatus.PENDING_PAYMENT,
        index=True,
        description="订单状态"
    )

    # 支付时间
    paid_at = fields.DatetimeField(null=True, description="支付时间")

    # 幂等性 Key
    # 设置 unique=True 对应 SQL 的 UNIQUE INDEX
    idempotency_key = fields.CharField(
        max_length=128,
        null=True,
        unique=True,
        description="幂等性去重键"
    )

    # 扩展字段 (JSONB)
    # default=dict 对应 SQL 的 DEFAULT '{}'
    snapshot_info = fields.JSONField(default=dict, description="商品快照")
    extra_data = fields.JSONField(default=dict, description="支付回调/二维码等扩展数据")

    # 审计字段
    client_ip = fields.CharField(max_length=64, null=True, description="下单IP")
    is_deleted = fields.BooleanField(default=False, description="软删除")

    # 时间字段 (自动管理)
    # auto_now_add 对应 DEFAULT NOW()
    created_time = fields.DatetimeField(auto_now_add=True, description="创建时间")
    # auto_now 对应 触发器自动更新逻辑
    updated_time = fields.DatetimeField(auto_now=True, description="更新时间")

    class Meta:
        table = "orders"
        table_description = "课程购买订单表"

    def __str__(self):
        return f"Order({self.order_no}, Status: {self.status})"