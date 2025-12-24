from tortoise import fields, models, timezone

class File(models.Model):
    """
    文件信息表
    """
    id = fields.BigIntField(pk=True, generated=True, description="主键ID")
    uploader_id = fields.BigIntField(description="上传者ID")
    module = fields.BigIntField(null=True, blank=True, description="模块类型")
    source_file_name = fields.CharField(max_length=255, description="源文件名")
    source_file_size = fields.BigIntField(description="源文件大小")
    source_file_type = fields.CharField(max_length=50, description="源文件类型")
    file_name = fields.CharField(max_length=255, description="存储文件名")
    file_path = fields.CharField(max_length=500, description="文件存储路径")
    created_time = fields.DatetimeField(auto_now_add=True, default=timezone.now, description="创建时间")
    updated_time = fields.DatetimeField(auto_now=True, default=timezone.now, description="更新时间")
    is_deleted = fields.BooleanField(default=False, description="是否删除")

    class Meta:
        table = "file"
        # schema = "medical_pulse_communication"
        table_description = "文件表"