import logging
from typing import AsyncGenerator, Optional
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
    AsyncSession,
    AsyncEngine
)
import redis.asyncio as aioredis
from redis.asyncio import Redis, ConnectionPool

from .config import db_config
from .models import Base

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages SQLAlchemy async engine and session lifecycle with connection pooling."""

    def __init__(self):
        self._engine: Optional[AsyncEngine] = None
        self._sessionmaker: Optional[async_sessionmaker[AsyncSession]] = None

    def get_engine(self) -> AsyncEngine:
        if self._engine is None:
            url = db_config.db.database_url
            is_sqlite = "sqlite" in url

            engine_kwargs = {
                "echo": db_config.db.echo,
                "future": True
            }

            if not is_sqlite:
                engine_kwargs.update({
                    "pool_size": db_config.db.pool_size,
                    "max_overflow": db_config.db.max_overflow,
                    "pool_recycle": db_config.db.pool_recycle,
                    "pool_timeout": db_config.db.pool_timeout,
                    "pool_pre_ping": True,
                })

            self._engine = create_async_engine(url, **engine_kwargs)
            self._sessionmaker = async_sessionmaker(
                bind=self._engine,
                expire_on_commit=False,
                class_=AsyncSession
            )
            logger.info(f"DatabaseManager: Initialized async database engine for {url.split('@')[-1] if '@' in url else url}")
        return self._engine

    def get_sessionmaker(self) -> async_sessionmaker[AsyncSession]:
        if self._sessionmaker is None:
            self.get_engine()
        return self._sessionmaker

    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        """Provide a transactional async session scope."""
        sessionmaker = self.get_sessionmaker()
        async with sessionmaker() as sess:
            try:
                yield sess
                await sess.commit()
            except Exception:
                await sess.rollback()
                raise

    async def init_tables(self) -> None:
        """Create all tables if they do not already exist."""
        engine = self.get_engine()
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("DatabaseManager: Durable PostgreSQL/SQLite tables verified and ready.")

    async def close(self) -> None:
        """Dispose of the database connection pool."""
        if self._engine:
            await self._engine.dispose()
            self._engine = None
            self._sessionmaker = None
            logger.info("DatabaseManager: Disposed database engine.")


class RedisManager:
    """Manages distributed Redis connection pool and provides resilient operations."""

    def __init__(self):
        self._pool: Optional[ConnectionPool] = None
        self._client: Optional[Redis] = None
        self._is_available: bool = False

    async def get_client(self) -> Optional[Redis]:
        if not db_config.redis.enabled:
            return None

        if self._client is None:
            try:
                self._pool = ConnectionPool.from_url(
                    db_config.redis.redis_url,
                    max_connections=db_config.redis.max_connections,
                    socket_connect_timeout=db_config.redis.connection_timeout,
                    socket_timeout=db_config.redis.connection_timeout,
                    decode_responses=True
                )
                self._client = Redis(connection_pool=self._pool)
                # Quick health check ping
                await self._client.ping()
                self._is_available = True
                logger.info(f"RedisManager: Connected to Redis at {db_config.redis.redis_url}")
            except Exception as e:
                logger.warning(f"RedisManager: Redis unavailable ({e}). Gracefully falling back to durable PostgreSQL queries.")
                self._is_available = False
                self._client = None

        return self._client

    @property
    def is_available(self) -> bool:
        return self._is_available

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None
        if self._pool:
            await self._pool.disconnect()
            self._pool = None
        self._is_available = False
        logger.info("RedisManager: Closed Redis connection pool.")


# Global instances
db_manager = DatabaseManager()
redis_manager = RedisManager()
