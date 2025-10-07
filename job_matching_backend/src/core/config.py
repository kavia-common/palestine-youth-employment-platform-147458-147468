from functools import lru_cache
from typing import List, Optional

from pydantic import Field, AnyHttpUrl, AliasChoices
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
    # Make optional to avoid import-time crashes. We'll validate at DB access.
    DATABASE_URL: Optional[str] = Field(default=None, description="Postgres connection URI for Supabase Postgres")
    # Optional fallback: some environments provide a DIRECT_URL without pgbouncer. We may try this if primary fails.
    DIRECT_URL: Optional[str] = Field(default=None, description="Optional direct Postgres connection URI (fallback)")

    # Supabase
    SUPABASE_URL: Optional[AnyHttpUrl] = Field(
        default=None,
        description="Supabase project URL",
    )
    # Accept multiple env var spellings: SUPABASE_SERVICE_KEY (preferred) and SUPABASE_KEY / supabase_key (legacy).
    SUPABASE_SERVICE_KEY: Optional[str] = Field(
        default=None,
        description="Supabase service role key",
        validation_alias=AliasChoices("SUPABASE_SERVICE_KEY", "SUPABASE_KEY", "supabase_key"),
    )
    SUPABASE_ANON_KEY: Optional[str] = Field(
        default=None,
        description="Supabase anon key for client features",
        validation_alias=AliasChoices("SUPABASE_ANON_KEY", "supabase_anon_key"),
    )
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

    # Pydantic v2 settings: no env prefix, ignore extra unknown vars to prevent extra_forbidden
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False, env_prefix="", extra="ignore")

    # PUBLIC_INTERFACE
    def require_database_url(self) -> str:
        """
        Return DATABASE_URL or raise a clear, actionable error message.

        Notes:
        - The database module will normalize postgres/postgresql URLs to use the psycopg v3 driver
          (postgresql+psycopg://).
        - If 'sslmode' is not specified in the URL, it is enforced to 'require' for compatibility with Supabase.
        """
        if self.DATABASE_URL:
            return self.DATABASE_URL
        # Provide helpful guidance about configuration.
        raise RuntimeError(
            "DATABASE_URL is not configured. Provide a Postgres connection string via DATABASE_URL. "
            "If you intend to rely on Supabase, ensure your Supabase project provides a database URL "
            "and set it here. Environment variables acknowledged: DATABASE_URL, SUPABASE_URL, "
            "SUPABASE_SERVICE_KEY/ANON_KEY. Note: The backend requires DATABASE_URL when accessing the DB."
        )


# PUBLIC_INTERFACE
def get_cors_origins(settings: Settings) -> List[str]:
    """Return parsed list of CORS origins from settings.

    Behavior:
    - If CORS_ORIGINS is "*" allow all.
    - In development (APP_ENV=development), ensure http://localhost:3000 is included for local frontend dev,
      unless "*" is used or it is already present.
    - Use /api/debug/cors to inspect effective values at runtime.
    """
    raw = settings.CORS_ORIGINS.strip()
    if not raw or raw == "*":
        return ["*"]
    origins = [o.strip() for o in raw.split(",") if o.strip()]
    if settings.APP_ENV.lower() == "development":
        if "http://localhost:3000" not in origins:
            # Ensure local frontend can reach backend during dev
            origins.append("http://localhost:3000")
    return origins


# PUBLIC_INTERFACE
@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Get cached application settings from environment."""
    return Settings()
