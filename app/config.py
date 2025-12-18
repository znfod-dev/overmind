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
    database_echo: bool = False  # Set to True for SQL logging

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


# 싱글톤 설정 인스턴스
settings = Settings()
