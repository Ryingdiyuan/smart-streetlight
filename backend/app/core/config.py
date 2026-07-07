from functools import lru_cache
from urllib.parse import quote_plus

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "智慧路灯节能系统后端"
    app_version: str = "0.1.0"
    debug: bool = True
    api_prefix: str = "/api"

    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]

    mysql_host: str = "127.0.0.1"
    mysql_port: int = 3307
    mysql_user: str = "root"
    mysql_password: str = Field(default="", repr=False)
    mysql_database: str = "smart_streetlight"

    mqtt_enabled: bool = False
    mqtt_host: str = "127.0.0.1"
    mqtt_port: int = 1883
    mqtt_username: str | None = None
    mqtt_password: str | None = Field(default=None, repr=False)
    mqtt_client_id: str = "smart-streetlight-backend"

    scheduler_enabled: bool = True
    device_offline_seconds: int = 180

    cloud_db_enabled: bool = False
    cloud_mysql_host: str = "127.0.0.1"
    cloud_mysql_port: int = 3306
    cloud_mysql_user: str = "root"
    cloud_mysql_password: str = Field(default="", repr=False)
    cloud_mysql_database: str = "smart_streetlight"
    db_sync_interval_seconds: int = 30

    llm_enabled: bool = False
    llm_provider: str = "openai-compatible"
    llm_api_key: str = Field(default="", repr=False)
    llm_base_url: str = ""
    llm_model: str = ""
    llm_timeout_seconds: int = 30

    jwt_secret_key: str = Field(default="please-change-this-in-local-env", repr=False)
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 120

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    @property
    def database_url(self) -> str:
        password = quote_plus(self.mysql_password)
        return (
            f"mysql+pymysql://{self.mysql_user}:{password}"
            f"@{self.mysql_host}:{self.mysql_port}/{self.mysql_database}"
            "?charset=utf8mb4"
        )

    @property
    def cloud_database_url(self) -> str:
        password = quote_plus(self.cloud_mysql_password)
        return (
            f"mysql+pymysql://{self.cloud_mysql_user}:{password}"
            f"@{self.cloud_mysql_host}:{self.cloud_mysql_port}/{self.cloud_mysql_database}"
            "?charset=utf8mb4"
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
