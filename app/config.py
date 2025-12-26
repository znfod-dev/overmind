"""환경 변수 및 설정 관리"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """애플리케이션 설정"""

    # API Keys
    anthropic_api_key: str = ""
    google_ai_api_key: str = ""
    openai_api_key: str = ""

    # Server Settings
    app_name: str = "Overmind AI Gateway"
    debug: bool = False

    # API Authentication
    api_auth_key: str = ""

    # Internal Service Authentication
    internal_api_key: str = ""

    # Service URLs
    ai_service_url: str = "http://localhost:8000"

    # JWT Configuration
    jwt_secret_key: str = "your-secret-key-change-in-production"  # CHANGE THIS!
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 10080  # 7 days (for development)

    # Database Configuration
    database_url: str = "sqlite+aiosqlite:///./data/overmind.db"  # Default to SQLite
    cloud_sql_connection_name: str | None = None
    database_echo: bool = False  # Set to True for SQL logging

    # Google Cloud Storage Configuration
    gcs_bucket_name: str | None = None  # GCS bucket name for image storage
    gcs_credentials_path: str | None = None  # Path to GCS service account JSON
    local_storage_path: str = "./storage/images"  # Fallback local storage path

    # Image Upload Settings
    max_image_size_mb: int = 5  # Maximum image file size in MB
    allowed_image_types: list[str] = ["image/jpeg", "image/png", "image/webp", "image/heic"]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="allow",  # Allow extra fields from .env
    )


# 싱글톤 설정 인스턴스
settings = Settings()
