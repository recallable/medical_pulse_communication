from tortoise import models, fields


class MedicalRecord(models.Model):
    """
    病历表（适配 ES 同步，支持疾病 / 症状 / 治疗关键字搜索）
    """

    # ==================== 1. 基础标识字段 ====================
    id = fields.IntField(pk=True, description="主键ID，自增")

    record_no = fields.CharField(
        max_length=50,
        unique=True,
        description="病历编号（唯一，ES同步主键）"
    )

    # ==================== 2. 核心可搜索字段 ====================
    disease_name = fields.CharField(
        max_length=200,
        description="疾病名称（核心检索字段）"
    )

    symptoms = fields.TextField(
        description="核心症状（核心检索字段）"
    )

    treatment_plan = fields.TextField(
        description="治疗方案（核心检索字段）"
    )

    diagnosis_conclusion = fields.TextField(
        null=True,
        description="诊断结论（完整文本，支持全文检索）"
    )

    # ==================== 3. 患者基础信息 ====================
    patient_name = fields.CharField(
        max_length=50,
        description="患者姓名"
    )

    patient_gender = fields.CharField(
        max_length=10,
        description="患者性别：男/女/未知"
    )

    patient_age = fields.IntField(
        description="患者年龄"
    )

    patient_id = fields.CharField(
        max_length=32,
        unique=True,
        description="患者唯一编号（医院内建档编号）"
    )

    # ==================== 4. 诊疗核心信息 ====================
    department = fields.CharField(
        max_length=50,
        description="就诊科室"
    )

    visit_type = fields.CharField(
        max_length=20,
        description="就诊类型：门诊/住院/急诊"
    )

    admission_time = fields.DatetimeField(
        null=True,
        description="入院时间"
    )

    discharge_time = fields.DatetimeField(
        null=True,
        description="出院时间"
    )

    doctor_name = fields.CharField(
        max_length=50,
        description="主治医生姓名"
    )

    # ==================== 5. 扩展灵活字段 ====================
    extend_info = fields.JSONField(
        null=True,
        description="扩展非标信息（JSONB，如检查指标、特殊医嘱、并发症等）"
    )

    # ==================== 6. 审计字段 ====================
    is_deleted = fields.BooleanField(
        default=False,
        description="逻辑删除标识"
    )

    created_time = fields.DatetimeField(
        auto_now_add=True,
        description="数据创建时间"
    )

    updated_time = fields.DatetimeField(
        auto_now=True,
        description="数据更新时间"
    )

    class Meta:
        table = "medical_record"
        # schema = "medical_pulse_communication"
        table_description = "病历表（适配ES同步，支持疾病/症状/治疗关键字搜索）"
