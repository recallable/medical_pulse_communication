import decimal

from tortoise import fields, models
from tortoise.validators import Validator, ValidationError


# -------------------------- 自定义CHECK约束验证器 --------------------------
class DifficultyLevelValidator(Validator):
    """难度等级验证器（1-4）"""

    def __call__(self, value: int):
        if value not in (1, 2, 3, 4):
            raise ValidationError(f"难度等级必须是1-4，当前值：{value}")


class NonNegativeValidator(Validator):
    """非负数验证器（≥0）"""

    def __call__(self, value):
        if value < 0:
            raise ValidationError(f"值必须≥0，当前值：{value}")


class CreatorIdValidator(Validator):
    """创建人ID验证器（>0）"""

    def __call__(self, value: int):
        if value <= 0:
            raise ValidationError(f"创建人ID必须>0，当前值：{value}")


class SaleStatusValidator(Validator):
    """售卖状态验证器（0-2）"""

    def __call__(self, value: int):
        if value not in (0, 1, 2):
            raise ValidationError(f"售卖状态必须是0-2，当前值：{value}")


class DataStatusValidator(Validator):
    """数据状态验证器（0-2）"""

    def __call__(self, value: int):
        if value not in (0, 1, 2):
            raise ValidationError(f"数据状态必须是0-2，当前值：{value}")


# -------------------------- 核心实体类映射 --------------------------
class MedicalCourse(models.Model):
    """
    医疗商业课程表（对应medical_pulse_communication.medical_course）
    """
    # 主键字段（自增BIGINT，对应PostgreSQL的IDENTITY）
    id = fields.BigIntField(pk=True, generated=True, description="课程唯一主键")

    # 课程编码（唯一约束，非空）
    course_code = fields.CharField(max_length=32, unique=True, null=False, description="课程编码（如：MED-CARDIO-202501）")

    # 课程名称（非空）
    course_name = fields.CharField(max_length=128, null=False, description="课程名称（如：心内科临床诊疗进阶）")

    # 医疗专科（非空）
    medical_department = fields.CharField(max_length=64, null=False, description="医疗专科（如：心内科、呼吸科、妇产科）")

    # 适用职称/岗位
    applicable_title = fields.CharField(max_length=128, null=True,
                                        description="适用职称/岗位（如：住院医师、主治医师、护士）")

    # 报名资质要求
    qualification_req = fields.CharField(max_length=255, null=True,
                                         description="报名资质要求（如：需执业医师证、护士资格证）")

    # 合规备案编号
    compliance_record_no = fields.CharField(max_length=64, null=True, description="医疗课程合规备案编号（行业监管必填）")

    # 难度等级（默认2，1-4）
    difficulty_level = fields.SmallIntField(default=2, null=False, validators=[DifficultyLevelValidator()],
                                            description="难度等级（1-入门，2-进阶，3-高阶，4-专家）")

    # 总课时（默认0.0，≥0）
    class_hours = fields.DecimalField(max_digits=5, decimal_places=1, default=decimal.Decimal("0.0"), null=False,
                                      validators=[NonNegativeValidator()], description="课程总课时（如：16.5课时）")

    # 继续教育学分（默认0.0，≥0）
    credit = fields.DecimalField(max_digits=3, decimal_places=1, default=decimal.Decimal("0.0"), null=True,
                                 validators=[NonNegativeValidator()], description="继续教育学分（医疗行业特有）")

    # 课程售价（默认0.00，≥0）
    price = fields.DecimalField(max_digits=10, decimal_places=2, default=decimal.Decimal("0.00"), null=False,
                                validators=[NonNegativeValidator()], description="课程售价（元）")

    # 售卖状态（默认1，0-下架，1-在售，2-预售）
    sale_status = fields.SmallIntField(default=1, null=False, validators=[SaleStatusValidator()],
                                       description="售卖状态（0-下架，1-在售，2-预售）")

    # 有效期（默认365天，≥0，0=永久）
    valid_period_days = fields.IntField(default=365, null=False, validators=[NonNegativeValidator()],
                                        description="课程购买后有效期（天，0表示永久有效）")

    # 退款规则
    refund_rule = fields.CharField(max_length=512, null=True, description="退款规则（如：开课7天内可退，超过不可退）")

    # 课程详细描述
    course_desc = fields.TextField(null=True, description="课程详细描述")

    # 数据状态（默认1，0-禁用，1-启用，2-删除）
    status = fields.SmallIntField(default=1, null=False, validators=[DataStatusValidator()],
                                  description="数据状态（0-禁用，1-启用，2-删除）")

    # 创建人ID（>0）
    creator_id = fields.BigIntField(null=False, validators=[CreatorIdValidator()], description="创建人ID（关联用户表）")

    # 是否删除（默认False）
    is_deleted = fields.BooleanField(default=False, null=True, description="是否删除（true-已删除 false-未删除）")

    # 创建时间（自动生成，带时区）
    created_time = fields.DatetimeField(auto_now_add=True, timezone=True, null=False, description="创建时间")

    # 更新时间（自动更新，带时区）
    updated_time = fields.DatetimeField(auto_now=True, timezone=True, null=False, description="更新时间")

    # 扩展字段（JSONB）
    ext_info = fields.JSONField(null=True, description="扩展字段（存储临时/个性化信息，如分销比例）")

    # -------------------------- 元数据配置 --------------------------
    class Meta:
        # 指定数据库模式+表名（匹配PostgreSQL）
        table = "medical_course"
        table_description = "好友表"