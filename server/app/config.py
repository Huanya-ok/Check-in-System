from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings

SERVER_DIR = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    app_name: str = "Face Check-in System"
    debug: bool = True

    database_url: str = "postgresql+asyncpg://checkin:checkin@localhost:5432/checkin"
    redis_url: str = "redis://localhost:6379/0"

    secret_key: str = "change-me-in-production-use-env-var"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24

    face_similarity_threshold: float = 0.93

    upload_dir: str = "uploads"
    faiss_index_path: str = "data/face_index.faiss"

    # 华为云 FRS 配置（卞浩宇负责申请与调试）
    huaweicloud_sdk_ak: str = ""
    huaweicloud_sdk_sk: str = ""
    huawei_ak: str = ""
    huawei_sk: str = ""
    huawei_face_endpoint: str = ""
    huawei_region: str = "cn-east-3"
    huawei_project_id: str = ""
    huawei_frs_region: str = "cn-east-3"
    huawei_face_set_name: str = ""

    @field_validator("debug", mode="before")
    @classmethod
    def parse_debug(cls, value):
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in {"release", "prod", "production", "false", "0", "no", "off"}:
                return False
            if normalized in {"debug", "dev", "development", "true", "1", "yes", "on"}:
                return True
        return value

    class Config:
        env_file = SERVER_DIR / ".env"
        extra = "ignore"


settings = Settings()
