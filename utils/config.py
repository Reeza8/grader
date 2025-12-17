from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    JWT_SECRET_KEY: str
    DATABASE_URL: str
    SYNC_ENGINE: str


    class Config:
        env_file = ".env"

settings = Settings()