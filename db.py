from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from utils.config import settings


# DATABASE_URL = "postgresql+asyncpg://root:4C5pt5Lnpae3Ewjw3bPVoYAZ@mydatabase:5432/postgres"

# sync_engine = create_engine("postgresql://root:4C5pt5Lnpae3Ewjw3bPVoYAZ@mydatabase:5432/postgres")
sync_engine = create_engine(settings.SYNC_ENGINE)
engine = create_async_engine(settings.DATABASE_URL, echo=False)

# for application

# Async session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, class_=AsyncSession, expire_on_commit=False)

async def get_async_session() -> AsyncSession:
    async with SessionLocal() as session:
        yield session


Base = declarative_base()
