from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    DATABASE_URL: str = Field("sqlite+aiosqlite:///./dev.db", env="DATABASE_URL")
    JWT_SECRET_KEY: str = Field("change-me-secret-key", env="JWT_SECRET_KEY")
    JWT_ALGORITHM: str = Field("HS256", env="JWT_ALGORITHM")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(60 * 24, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    BACKEND_URL: str = Field("http://localhost:8000", env="BACKEND_URL")

    class Config:
        env_file = ".env"


settings = Settings()
