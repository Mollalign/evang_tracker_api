import ssl
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from sqlalchemy.orm import declarative_base
from sqlalchemy import text
from sqlalchemy.dialects.postgresql.asyncpg import AsyncAdapt_asyncpg_dbapi
import logging
from typing import AsyncGenerator

# Logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Base
Base = declarative_base()

# -----------------------------
# Async Engine Setup (Neon + asyncpg)
# -----------------------------
if settings.DATABASE_URL.startswith("sqlite"):
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=False,
        future=True
    )
else:
    # SSL context for Neon
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = True
    ssl_context.verify_mode = ssl.CERT_REQUIRED

    engine_kwargs = {
        "echo": False,
        "future": True,
        "pool_size": 10,
        "max_overflow": 5,
        "pool_timeout": 30,
        "pool_pre_ping": True,
        "pool_recycle": 3600,
        "connect_args": {
            "ssl": ssl_context,
            "server_settings": {
                "application_name": "evang_tracker_api",
            }
        },
    }

    engine = create_async_engine(
        settings.DATABASE_URL.split("?")[0],  # remove sslmode & channel_binding from URL
        **engine_kwargs
    )

# Session factory
AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# FastAPI dependency
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Get database session.
    
    Note: If you encounter InvalidCachedStatementError after running migrations,
    restart the FastAPI server to clear the connection pool cache.
    Alternatively, call invalidate_connection_pool() to clear cached statements.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

# DB Initialization
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created successfully.")

# PostgreSQL Extensions
async def create_db_extensions():
    try:
        async with engine.begin() as conn:
            await conn.execute(text('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";'))
            await conn.execute(text('CREATE EXTENSION IF NOT EXISTS pgcrypto;'))
        logger.info("✅ PostgreSQL extensions created successfully.")
    except Exception as e:
        logger.error(f"Could not create extensions: {e}")

# Utilities
async def drop_all_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    logger.warning("⚠ All tables dropped (development/testing only).")

async def check_db_connection() -> bool:
    try:
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT 1"))
            # fetch one row in async style
            row = result.first()
        logger.info("✅ Database connection healthy.")
        return row is not None
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False

# Utility function to invalidate connection pool
async def invalidate_connection_pool():
    """
    Invalidate the connection pool to clear cached prepared statements.
    Call this after running Alembic migrations while the server is running.
    
    Usage:
        from app.core.database import invalidate_connection_pool
        await invalidate_connection_pool()
    """
    logger.info("Invalidating connection pool to clear cached statements...")
    await engine.dispose()
    logger.info("✅ Connection pool invalidated. New connections will be created on next request.")

# Database Manager
class DatabaseManager:
    @staticmethod
    async def reset_database():
        # await drop_all_tables()
        await init_db()
        await create_db_extensions()
        logger.info("✅ Database reset completed.")

    @staticmethod
    async def health_check() -> bool:
        return await check_db_connection()
    
    @staticmethod
    async def invalidate_pool():
        """Invalidate connection pool after schema changes."""
        await invalidate_connection_pool()
