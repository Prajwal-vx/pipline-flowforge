from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import model_validator

class Settings(BaseSettings):
    app_name: str = "FlowForge"
    environment: str = "development"
    database_url: str = "sqlite+aiosqlite:///./flowforge.db"
    redis_url: str = "redis://localhost:6379/0"
    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = 60 * 24
    cors_origins: str = "http://localhost:5173"
    openai_api_key: str = ""
    
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @model_validator(mode="after")
    def validate_security_settings(self):
        if self.environment.lower() in {"production", "prod"} and self.jwt_secret in {"change-me-in-production", "replace-with-a-long-random-secret"}:
            raise ValueError("JWT_SECRET must be changed before running in production")
        return self

    @property
    def cors_list(self):
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]

@lru_cache
def get_settings() -> Settings:
    return Settings()

settings = get_settings()
