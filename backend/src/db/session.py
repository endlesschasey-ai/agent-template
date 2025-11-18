"""Database session management."""
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from ..config import settings
from ..utils.logger import get_logger
from .base import Base

logger = get_logger(__name__)

# 创建同步引擎（用于初始化表）
sync_engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.SQLALCHEMY_ECHO,
    connect_args={"check_same_thread": False}  # SQLite 特定配置
)

# 创建异步引擎
async_database_url = settings.DATABASE_URL.replace("sqlite:///", "sqlite+aiosqlite:///")
async_engine = create_async_engine(
    async_database_url,
    echo=settings.SQLALCHEMY_ECHO,
    connect_args={"check_same_thread": False}
)

# 创建异步会话工厂
AsyncSessionLocal = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)


def init_db():
    """初始化数据库表"""
    # 导入所有模型以注册到 Base.metadata
    from ..models.db import session, message, file  # noqa: F401

    logger.info("Creating database tables if they don't exist...")
    Base.metadata.create_all(bind=sync_engine)
    logger.info("Database initialized successfully")


@asynccontextmanager
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """获取异步数据库会话"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
