from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "on-site-repair"
    redis_url: str = "redis://localhost:6379/0"
    # Tortoise ORM 使用的 DSN 格式通常为 postgres://user:pass@host:port/db
    database_url: str = "postgres://postgres:121518@localhost:5432/postgres"
    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    minio_secure: bool = False
    minio_bucket: str = "default"
    secret_key: str = "your-secret-key-here"  # JWT 密钥，生产环境请修改
    algorithm: str = "HS256"  # JWT 算法
    access_token_expire_minutes: int = 30  # Token 过期时间
    rong_lian_acc_id: str = '2c94811c9860a9c4019a0adbdb5e3ece'
    rong_lian_acc_token: str = '904da2c0751f444ca891743d9abf3be5'
    rong_lian_app_id: str = '2c94811c9860a9c4019a0adbdceb3ed5'
    dingtalk_client_id: str = 'dingafymrinlfauc6vpw'
    dingtalk_client_secret: str = 'EtZi9mcq59x-C42nwMugfzLxHQe1TrTeTNFhV98rH1jlacnhX-ByIDKA7e2WW_Vk'
    baidu_ocr_app_key: str = 'XAyedW0rHJl6YjYQQ5IAf7KC'
    baidu_ocr_secret_key: str = 'XvC5eNswoMBE6vQfvBLJavxuygL0iy4Z'
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def tortoise_config(self) -> dict:
        return {
            "connections": {"default": self.database_url},
            "use_tz": True,
            "timezone": "Asia/Shanghai",
            "apps": {
                "models": {
                    "models": ["models", "aerich.models"],
                    "default_connection": "default",
                }
            },
        }


settings = Settings()
