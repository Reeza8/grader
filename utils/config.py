from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache




class Settings(BaseSettings):
    JWT_SECRET_KEY: str
    DATABASE_URL: str
    SYNC_ENGINE: str

    model_config = SettingsConfigDict(
        env_file=".env",
        env_ignore_empty=True
    )

@lru_cache
def get_settings():
    return Settings()

settings = get_settings()
