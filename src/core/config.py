import os

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    API_KEY: str
    BASE_URL: str
    
    # Делаем DATABASE_URL необязательным, так как платформа может дать его по частям
    DATABASE_URL: str | None = None

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    def get_database_url(self) -> str:
        if self.DATABASE_URL:
            return self.DATABASE_URL
            
        host = os.getenv("POSTGRES_HOST", "localhost")
        port = os.getenv("POSTGRES_PORT", "5432")
        # Платформа может передавать username как USERNAME, так и USER
        user = os.getenv("POSTGRES_USERNAME") or os.getenv("POSTGRES_USER", "postgres")
        password = os.getenv("POSTGRES_PASSWORD", "postgres")
        dbname = os.getenv("POSTGRES_DATABASE_NAME", "events_db")
        
        return f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{dbname}"

settings = Settings()