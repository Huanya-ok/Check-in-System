from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Face Check-in System"
    debug: bool = True

    database_url: str = "postgresql+asyncpg://checkin:checkin@localhost:5432/checkin"
    redis_url: str = "redis://localhost:6379/0"

    secret_key: str = "change-me-in-production-use-env-var"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24

    face_similarity_threshold: float = 0.8

    upload_dir: str = "uploads"

    # 华为云 FRS 配置（卞浩宇负责申请与调试）
    huawei_ak: str = ""
    huawei_sk: str = ""
    huawei_project_id: str = ""
    huawei_frs_region: str = "cn-north-4"
    huawei_face_set_name: str = "checkin_face_set"

    class Config:
        env_file = ".env"


settings = Settings()
