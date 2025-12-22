from tortoise import fields, models

class User(models.Model):
    """
    用户信息表
    """
    # 主键ID（自增大整数）
    id = fields.BigIntField(pk=True, generated=True, description="主键ID")
    # 用户账号（最大长度20）
    username = fields.CharField(max_length=20, null=True, blank=True, description="用户账号")
    # 用户手机号（登录账号，最大长度20）
    phone = fields.CharField(max_length=20, null=True, blank=True, description="用户手机号（登录账号）")
    # 加密后的登录密码（MD5/BCrypt，最大长度100）
    password = fields.CharField(max_length=100, null=True, blank=True, description="加密后的登录密码（MD5/BCrypt）")
    # 用户昵称（最大长度50）
    nickname = fields.CharField(max_length=50, null=True, blank=True, description="用户昵称")
    # 用户头像ID（关联files.id，大整数）
    avatar_id = fields.BigIntField(null=True, blank=True, description="用户头像ID（单文件，关联files.id）")
    # 用户性别（0-未知 1-男 2-女，默认0）
    gender = fields.SmallIntField(default=0, description="用户性别（0-未知 1-男 2-女）")
    # 用户状态（0-禁用 1-正常，默认1）
    user_status = fields.SmallIntField(default=1, description="用户状态（0-禁用 1-正常）")
    # 最后登录时间
    last_login_time = fields.DatetimeField(null=True, blank=True, description="最后登录时间")
    # 是否删除（true-已删除 false-未删除，默认False）
    is_deleted = fields.BooleanField(default=False, description="是否删除（true-已删除 false-未删除）")
    # 创建时间（默认当前时间）
    created_time = fields.DatetimeField(auto_now_add=True, description="创建时间")
    # 更新时间（自动更新，默认当前时间）
    updated_time = fields.DatetimeField(auto_now=True, description="更新时间（自动更新）")

    class Meta:
        # 数据库表名（包含模式名）
        table = "user"
        # 数据库模式名（对应 PostgreSQL 的 schema）
        schema = "medical_pulse_communication"
        # 索引配置（可根据需求添加）
        # indexes = [
        #     # 手机号索引（登录常用，提高查询效率）
        #     ("idx_user_phone", ["phone"]),
        #     # 用户名索引
        #     ("idx_user_username", ["username"]),
        # ]
        # # 唯一约束（可选，根据业务需求）
        # unique_together = [
        #     # 确保手机号唯一（如果业务要求）
        #     # ("phone",)
        # ]
