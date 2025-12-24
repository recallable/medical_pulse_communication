from tortoise import fields, models, timezone


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
    created_time = fields.DatetimeField(auto_now_add=True, default=timezone.now, description="创建时间")
    # 更新时间（自动更新，默认当前时间）
    updated_time = fields.DatetimeField(auto_now=True, default=timezone.now, description="更新时间（自动更新）")
    identity = fields.BooleanField(default=False, description="是否认证")
    identity_card = fields.CharField(max_length=100, null=True, blank=True, description="身份证号")
    id_card_front_id = fields.BigIntField(null=True, blank=True, description="身份证正面文件ID")
    id_card_back_id = fields.BigIntField(null=True, blank=True, description="身份证反面文件ID")
    user_identity = fields.BigIntField(null=True, blank=True, description="用户身份")

    class Meta:
        # 数据库表名（包含模式名）
        table = "user"
        # 数据库模式名（对应 PostgreSQL 的 schema）
        # schema = "medical_pulse_communication"
        table_description = "用户表"


class UserThirdParty(models.Model):
    """
    用户第三方登录关联表
    """
    # 主键ID（自增大整数）
    id = fields.BigIntField(pk=True, generated=True, description="主键ID")
    # 关联用户ID（外键）
    user = fields.ForeignKeyField(model_name="models.User", related_name="third_party_bindings", field_name="user_id",
                                  on_delete=fields.CASCADE, description="关联的用户ID（外键）")
    # 第三方平台（如wechat/qq）
    third_platform = fields.CharField(max_length=20, description="第三方平台（wechat/qq/github/alipay等）")
    # 第三方openid（用户唯一标识）
    third_openid = fields.CharField(max_length=100, description="第三方平台的用户唯一标识（openid）")
    # 第三方unionid（跨应用唯一标识，可选）
    third_unionid = fields.CharField(max_length=100, null=True, description="第三方平台的统一标识（unionid，跨应用）")
    # 第三方访问令牌（可选）
    access_token = fields.CharField(max_length=200, null=True, description="第三方访问令牌")
    # 第三方刷新令牌（可选）
    refresh_token = fields.CharField(max_length=200, null=True, description="第三方刷新令牌")
    # 令牌过期时间（秒，可选）
    expires_in = fields.IntField(null=True, description="令牌过期时间（秒）")
    # 创建时间（默认当前时间）
    created_time = fields.DatetimeField(auto_now_add=True, default=timezone.now, description="创建时间")
    # 更新时间（自动更新）
    updated_time = fields.DatetimeField(auto_now=True, default=timezone.now, description="更新时间")
    # 是否删除（软删，默认未删除）
    is_deleted = fields.BooleanField(default=False, description="是否删除（软删）")

    class Meta:
        # 数据库表名
        table = "user_third_party"
        # schema = "medical_pulse_communication"
        # 表注释
        table_description = "用户第三方登录关联表"
