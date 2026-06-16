from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Face Check-in System"
    debug: bool = True

    database_url: str = "postgresql+asyncpg://checkin:checkin@localhost:5432/checkin"
    redis_url: str = "redis://localhost:6379/0"

    secret_key: str = "change-me-in-production-use-env-var"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24

    face_similarity_threshold: float = 0.5
    check_in_cooldown_seconds: int = 30

    upload_dir: str = "uploads"
    faiss_index_path: str = "data/face_index.faiss"
    face_model_name: str = "buffalo_l"

    class Config:
        env_file = ".env"


settings = Settings()
