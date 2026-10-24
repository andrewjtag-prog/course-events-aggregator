import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    API_KEY: str
    BASE_URL: str
    
    # Делаем DATABASE_URL необязательным, так как платформа может дать его по частям
    DATABASE_URL: str | None = None

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    def get_database_url(self) -> str:
        # Если DATABASE_URL передан напрямую (локально), используем его
        if self.DATABASE_URL:
            return self.DATABASE_URL
            
        # Если мы на платформе, собираем URL из переменных, которые она дает
        host = os.getenv("POSTGRES_HOST", "localhost")
        port = os.getenv("POSTGRES_PORT", "5432")
        user = os.getenv("POSTGRES_USERNAME", "postgres")
        password = os.getenv("POSTGRES_PASSWORD", "postgres")
        dbname = os.getenv("POSTGRES_DATABASE_NAME", "events_db")
        
        # Обрати внимание на +asyncpg (наш драйвер)
        return f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{dbname}"

settings = Settings()