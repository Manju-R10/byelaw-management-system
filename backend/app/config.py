import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

import urllib.parse

class Settings(BaseSettings):
    # Load settings from .env file
    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Database Configuration
    DB_HOST: str = "127.0.0.1"
    DB_PORT: int = 3306
    DB_USER: str = "root"
    DB_PASSWORD: str = ""
    DB_NAME: str = "byelaw_db"

    # Security & JWT Configuration
    JWT_SECRET_KEY: str = "cdit-byelaw-secret-key-2026-secure-auth"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # File Upload Configuration
    UPLOAD_DIR: str = "C:\\Users\\Mahalakshmi\\.gemini\\antigravity\\scratch\\byelaw_management_system\\uploads"
    MAX_UPLOAD_SIZE_MB: int = 25

    # Application Settings
    ENV: str = "development"
    LOG_LEVEL: str = "INFO"
    PROJECT_NAME: str = "C-DIT Cooperative Society Bye-law Management System"
    API_V1_PREFIX: str = "/api/v1"

    # Comma-separated list of allowed CORS origins for the browser frontend.
    BACKEND_CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173"

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.BACKEND_CORS_ORIGINS.split(",") if origin.strip()]

    @property
    def database_url(self) -> str:
        # Returns standard sync URL (useful for migrations/alembic)
        encoded_password = urllib.parse.quote_plus(self.DB_PASSWORD)
        return f"mysql+pymysql://{self.DB_USER}:{encoded_password}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}?charset=utf8mb4"

    @property
    def async_database_url(self) -> str:
        # Returns async URL for FastAPI async operations
        encoded_password = urllib.parse.quote_plus(self.DB_PASSWORD)
        return f"mysql+aiomysql://{self.DB_USER}:{encoded_password}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}?charset=utf8mb4"

settings = Settings()
