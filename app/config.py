from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "sqlite+aiosqlite:///./app.db"
    jwt_secret: str = "change-me-in-production-seriously"
    jwt_algorithm: str = "HS256"
    access_token_ttl_minutes: int = 30
    app_name: str = "Course Platform"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    @property
    def async_database_url(self) -> str:
        url = self.database_url
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql+asyncpg://", 1)
        elif url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        return url


settings = Settings()
