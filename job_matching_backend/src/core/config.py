from functools import lru_cache
from typing import List, Optional

from pydantic import Field, AnyHttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # App
    APP_NAME: str = Field(default="YEP Job Matching API", description="Application name")
    APP_ENV: str = Field(default="development", description="Application environment")
    PORT: int = Field(default=8000, description="Port to run the API server")

    # CORS
    CORS_ORIGINS: str = Field(default="*", description="Comma separated list of allowed origins")

    # Database
    DATABASE_URL: str = Field(..., description="Postgres connection URI for Supabase Postgres")

    # Supabase
    SUPABASE_URL: Optional[AnyHttpUrl] = Field(default=None, description="Supabase project URL")
    SUPABASE_SERVICE_KEY: Optional[str] = Field(default=None, description="Supabase service role key")
    SUPABASE_ANON_KEY: Optional[str] = Field(default=None, description="Supabase anon key for client features")
    SUPABASE_JWT_SECRET: Optional[str] = Field(default=None, description="Supabase JWT secret for realtime channels")

    # Auth/JWT
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=60 * 24, description="Access token expiry in minutes")
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=30, description="Refresh token expiry in days")
    JWT_ALGORITHM: str = Field(default="HS256", description="JWT signing algorithm")
    JWT_SECRET_KEY: str = Field(default="local-dev-secret-change", description="JWT secret for API issued tokens")
    PASSWORD_HASH_SCHEME: str = Field(default="bcrypt", description="Password hashing scheme")

    # Providers
    EMBEDDINGS_PROVIDER: Optional[str] = Field(default=None, description="Embeddings provider name")
    EMBEDDINGS_API_KEY: Optional[str] = Field(default=None, description="Embeddings API Key")
    EMAIL_PROVIDER_API_KEY: Optional[str] = Field(default=None, description="Email provider API key")
    SMS_PROVIDER_API_KEY: Optional[str] = Field(default=None, description="SMS provider API key")

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)


# PUBLIC_INTERFACE
def get_cors_origins(settings: Settings) -> List[str]:
    """Return parsed list of CORS origins from settings."""
    raw = settings.CORS_ORIGINS.strip()
    if not raw or raw == "*":
        return ["*"]
    return [o.strip() for o in raw.split(",") if o.strip()]


# PUBLIC_INTERFACE
@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Get cached application settings from environment."""
    return Settings()
