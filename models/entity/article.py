from tortoise import models, fields


class Article(models.Model):
    """
    文章表（对应medical_pulse_communication.article）
    """

    id = fields.BigIntField(pk=True, generated=True, verbose_name="文章ID")
    title = fields.CharField(max_length=255, null=False, verbose_name="文章标题")
    url = fields.CharField(max_length=255, null=False, verbose_name="文章URL")
    thumb = fields.CharField(max_length=255, null=True, verbose_name="文章缩略图")
    description = fields.TextField(null=True, verbose_name="文章描述")
    type = fields.CharField(max_length=20, null=False, verbose_name="文章类型")
    input_time = fields.DatetimeField(null=False, use_tz=True, verbose_name="文章输入时间")
    comment_count = fields.IntField(null=False, default=0, verbose_name="文章评论数")
    content = fields.TextField(null=False, verbose_name="文章内容")
    is_deleted = fields.BooleanField(default=False, verbose_name="是否删除")
    created_time = fields.DatetimeField(auto_now_add=True, use_tz=True, verbose_name="创建时间")
    updated_time = fields.DatetimeField(auto_now=True, use_tz=True, verbose_name="更新时间")

    class Meta:
        """
        模型元数据：指定数据库和表名，匹配原结构
        """
        # 对应PostgreSQL的schema（数据库名）和表名
        table = "article"
        # 禁用自动生成的表名复数形式（Tortoise默认会把article变成articles）
        table_description = "文章表"
