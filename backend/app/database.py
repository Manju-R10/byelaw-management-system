import logging
from typing import AsyncGenerator
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config import settings

logger = logging.getLogger(__name__)

# Base class for SQLAlchemy ORM models
Base = declarative_base()

# Synchronous connection engine and sessionmaker (mainly for Alembic migrations, seeding)
try:
    sync_engine = create_engine(
        settings.database_url,
        pool_pre_ping=True,
        pool_recycle=3600
    )
    SessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=sync_engine
    )
except Exception as e:
    logger.error(f"Error creating synchronous engine: {e}")
    sync_engine = None
    SessionLocal = None

# Asynchronous connection engine and sessionmaker (for standard web endpoints)
try:
    async_engine = create_async_engine(
        settings.async_database_url,
        pool_pre_ping=True,
        pool_recycle=3600
    )
    AsyncSessionLocal = async_sessionmaker(
        bind=async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False
    )
except Exception as e:
    logger.error(f"Error creating asynchronous engine: {e}")
    async_engine = None
    AsyncSessionLocal = None

# Dependency to fetch asynchronous session for API requests
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    if AsyncSessionLocal is None:
        raise RuntimeError("Asynchronous database sessionmaker is not configured.")
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
