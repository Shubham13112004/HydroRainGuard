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

# Vercel serverless environment
# /tmp is the writable temporary directory.
if os.getenv("VERCEL"):
    database_url = "sqlite+aiosqlite:////tmp/hydro_rain_guard.db"


# ============================================================
# ENGINE
# ============================================================

engine = create_async_engine(
    database_url,
    echo=False,
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
# INITIALIZE DATABASE
# ============================================================

async def init_db():
    from models import db_models  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(
            Base.metadata.create_all
        )
