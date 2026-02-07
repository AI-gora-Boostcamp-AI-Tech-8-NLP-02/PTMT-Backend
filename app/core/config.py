"""Application Configuration - 환경 변수 로드 및 설정 관리"""

from functools import lru_cache
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """애플리케이션 설정"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # 애플리케이션 설정
    APP_NAME: str = "PTMT"
    APP_ENV: str = "development"
    DEBUG: bool = True

    # 서버 설정
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # 데이터베이스 설정
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/ptmt"

    # JWT 설정
    JWT_SECRET_KEY: str = "super-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Refresh Cookie 설정
    AUTH_REFRESH_COOKIE_NAME: str = "ptmt_refresh_token"
    AUTH_REFRESH_COOKIE_PATH: str = "/api/auth"
    AUTH_REFRESH_COOKIE_SAMESITE: str = "lax"
    AUTH_REFRESH_COOKIE_SECURE: bool = False
    AUTH_REFRESH_COOKIE_DOMAIN: str | None = None

    # CORS 설정
    CORS_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000,http://localhost:3001,http://127.0.0.1:3001"

    @property
    def cors_origins_list(self) -> List[str]:
        """CORS origins를 리스트로 변환"""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    # Supabase 설정
    SUPABASE_URL: str = ""
    SUPABASE_ANON_KEY: str = ""
    SUPABASE_SERVICE_ROLE_KEY: str = ""

    # 파일 업로드 설정
    MAX_UPLOAD_SIZE_MB: int = 25
    STORAGE_PATH: str = "./storage"

    # 커리큘럼 생성 API (외부 서비스)
    CURRICULUM_GENERATION_API_URL: str = "http://curr.ptmt.site"
    CURRICULUM_GENERATION_API_TOKEN: str = Field(default="", env="CURRICULUM_GENERATION_API_TOKEN")
    
    # 키워드 추출 API (외부 서비스)
    KEYWORD_EXTRACTION_API_URL: str = "http://curr.ptmt.site"
    KEYWORD_EXTRACTION_API_TOKEN: str = Field(
        default="",
        env="KEYWORD_EXTRACTION_API_TOKEN",
    )

    # 키 슬롯 대기열 설정
    KEY_QUEUE_TOTAL_KEYS: int = 5
    KEY_QUEUE_COOLDOWN_SECONDS: int = 30
    KEY_QUEUE_CURRICULUM_COOLDOWN_SECONDS: int = 60
    KEY_QUEUE_MAX_BUSY_SECONDS: int = 600

    @property
    def max_upload_size_bytes(self) -> int:
        """최대 업로드 크기를 바이트로 변환"""
        return self.MAX_UPLOAD_SIZE_MB * 1024 * 1024


@lru_cache
def get_settings() -> Settings:
    """설정 인스턴스를 캐싱하여 반환"""
    return Settings()


settings = get_settings()
