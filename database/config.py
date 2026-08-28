import os
from typing import Optional
from pydantic import BaseModel, Field


class DatabaseSettings(BaseModel):
    """Database connection and pool configuration."""
    database_url: str = Field(
        default_factory=lambda: os.getenv(
            "DATABASE_URL",
            "sqlite+aiosqlite:///prepsense.db"
        )
    )
    sync_database_url: str = Field(
        default_factory=lambda: os.getenv(
            "SYNC_DATABASE_URL",
            "sqlite:///prepsense.db"
        )
    )
    pool_size: int = Field(default_factory=lambda: int(os.getenv("DB_POOL_SIZE", "10")))
    max_overflow: int = Field(default_factory=lambda: int(os.getenv("DB_MAX_OVERFLOW", "20")))
    pool_recycle: int = Field(default_factory=lambda: int(os.getenv("DB_POOL_RECYCLE", "1800")))
    pool_timeout: int = Field(default_factory=lambda: int(os.getenv("DB_POOL_TIMEOUT", "30")))
    echo: bool = Field(default_factory=lambda: os.getenv("DB_ECHO", "false").lower() == "true")


class RedisSettings(BaseModel):
    """Redis connection and distributed cache configuration."""
    redis_url: str = Field(
        default_factory=lambda: os.getenv(
            "REDIS_URL",
            "redis://localhost:6379/0"
        )
    )
    enabled: bool = Field(default_factory=lambda: os.getenv("REDIS_ENABLED", "true").lower() == "true")
    session_ttl_seconds: int = Field(default_factory=lambda: int(os.getenv("REDIS_SESSION_TTL", "86400")))  # 24 hours
    connection_timeout: float = Field(default_factory=lambda: float(os.getenv("REDIS_TIMEOUT", "2.0")))
    max_connections: int = Field(default_factory=lambda: int(os.getenv("REDIS_MAX_CONNECTIONS", "50")))


class PersistenceConfig(BaseModel):
    db: DatabaseSettings = Field(default_factory=DatabaseSettings)
    redis: RedisSettings = Field(default_factory=RedisSettings)


db_config = PersistenceConfig()
