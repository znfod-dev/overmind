"""Database configuration and session management"""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from pathlib import Path

from app.config import settings

# Get database URL from environment variables
DATABASE_URL = settings.database_url

# For SQLite, ensure data directory exists
if DATABASE_URL.startswith("sqlite"):
    DATABASE_DIR = Path(__file__).parent.parent.parent / "data"
    DATABASE_DIR.mkdir(exist_ok=True)

# Create async engine with appropriate settings for each database type
engine_kwargs = {
    "echo": settings.database_echo,
    "future": True,
}

# PostgreSQL specific settings
if DATABASE_URL.startswith("postgresql"):
    engine_kwargs.update({
        "pool_size": 5,
        "max_overflow": 10,
        "pool_pre_ping": True,  # Verify connections before using
        "pool_recycle": 3600,   # Recycle connections after 1 hour
    })

# Create async engine
engine = create_async_engine(DATABASE_URL, **engine_kwargs)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# Base class for models
Base = declarative_base()


async def get_db() -> AsyncSession:
    """
    Dependency for getting database session

    Usage:
        @router.get("/users")
        async def get_users(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    """Initialize database - create all tables"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db():
    """Close database engine"""
    await engine.dispose()
