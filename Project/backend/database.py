import os

from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker,
)
from sqlalchemy.orm import DeclarativeBase

from config import settings


# ============================================================
# DATABASE URL
# ============================================================

database_url = settings.database_url

# Vercel / Neon PostgreSQL
if os.getenv("VERCEL"):
    if database_url.startswith("postgresql://"):
        database_url = database_url.replace(
            "postgresql://",
            "postgresql+asyncpg://",
            1,
        )

    elif database_url.startswith("postgres://"):
        database_url = database_url.replace(
            "postgres://",
            "postgresql+asyncpg://",
            1,
        )


# ============================================================
# ENGINE
# ============================================================

engine = create_async_engine(
    database_url,
    echo=False,
    pool_pre_ping=True,
)


SessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# ============================================================
# BASE
# ============================================================

class Base(DeclarativeBase):
    pass


# ============================================================
# DATABASE SESSION
# ============================================================

async def get_db():
    async with SessionLocal() as session:
        yield session


# ============================================================
# INITIALIZE TABLES
# ============================================================

async def init_db():

    # Import models so SQLAlchemy knows about Assessment
    from models import db_models  # noqa: F401

    async with engine.begin() as conn:

        await conn.run_sync(
            Base.metadata.create_all
        )
