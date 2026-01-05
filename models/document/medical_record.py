from elasticsearch.dsl import Document, Text, Keyword, Integer, Date, Object, Boolean


class MedicalRecordDoc(Document):
    """
    ES 索引对应的 Python 模型类
    """
    # 1. 唯一标识
    record_no = Keyword()

    # 2. 核心搜索字段 (定义分词器)
    # 对应 mapping 中的 "analyzer": "ik_max_word"
    disease_name = Text(analyzer="ik_max_word", fields={'keyword': Keyword()})
    symptoms = Text(analyzer="ik_max_word")
    treatment_plan = Text(analyzer="ik_max_word")
    diagnosis_conclusion = Text(analyzer="ik_max_word")

    # 3. 患者信息
    patient_name = Text(analyzer="ik_max_word")
    patient_age = Integer()
    patient_gender = Keyword()

    # 4. 诊疗信息
    department = Keyword()
    doctor_name = Keyword()
    admission_time = Date()

    # 5. 扩展信息 (JSONB)
    extend_info = Object()

    # 6. 审计
    is_deleted = Boolean()

    class Index:
        # 指定对应的 ES 索引名
        name = 'medical_records'