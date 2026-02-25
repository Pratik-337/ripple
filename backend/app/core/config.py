from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # App
    environment: str = "development"
    secret_key: str = "change-me-in-production"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7

    # Database
    database_url: str = "postgresql+asyncpg://ripple:ripple@localhost:5432/ripple"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # MinIO / S3
    aws_access_key_id: str = "ripple"
    aws_secret_access_key: str = "ripple123"
    aws_s3_bucket: str = "ripple-files"
    aws_endpoint_url: str = "http://localhost:9000"
    aws_region: str = "us-east-1"

    # GitHub OAuth
    github_client_id: str = ""
    github_client_secret: str = ""
    github_redirect_uri: str = "http://localhost:8000/api/v1/auth/github/callback"

    # Ollama
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "deepseek-coder:6.7b"

    # CORS
    allowed_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    # Impact engine
    impact_engine_timeout: int = 60


settings = Settings()
