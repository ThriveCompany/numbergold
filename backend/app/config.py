from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    DATABASE_URL: str = Field("sqlite+aiosqlite:///./dev.db", env="DATABASE_URL")
    JWT_SECRET_KEY: str = Field("1b0836bfbb5065c7818a6b5d44f6bb9e", env="JWT_SECRET_KEY")
    JWT_ALGORITHM: str = Field("HS256", env="JWT_ALGORITHM")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(60 * 24, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    BACKEND_URL: str = Field("http://localhost:8000", env="BACKEND_URL")
    BACKEND_BASE_URL: str = Field("https://numbergold-backend.onrender.com", env="BACKEND_BASE_URL")

    class Config:
        env_file = ".env"


settings = Settings()
