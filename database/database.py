from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from typing import Callable
from config.db_config import settings
from utils.logger import logger

def get_url():
    user = settings.POSTGRES_USER
    password = settings.POSTGRES_PASSWORD
    server = settings.POSTGRES_SERVER
    db = settings.POSTGRES_DB
    port = settings.POSTGRES_PORT
    return f"postgresql+asyncpg://{user}:{password}@{server}:{port}/{db}"


SQLALCHEMY_DATABASE_URL = get_url()
engine = create_async_engine(SQLALCHEMY_DATABASE_URL)


AsyncSessionLocal: Callable[[], AsyncSession] = async_sessionmaker(
    autocommit=False, autoflush=False, bind=engine, class_=AsyncSession
)

Base = declarative_base()
