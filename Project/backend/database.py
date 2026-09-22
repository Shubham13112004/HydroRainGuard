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

database_url = settings.database_url.strip()


# ============================================================
# CONVERT POSTGRESQL → ASYNCPG
# ============================================================

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
# NEON / ASYNCPG CONNECTION
# ============================================================

connect_args = {}

if database_url.startswith("postgresql+asyncpg://"):

    # Neon connection URLs can contain parameters intended
    # for other PostgreSQL drivers/clients.
    #
    # asyncpg should receive SSL through connect_args instead
    # of sslmode/channel_binding URL parameters.

    database_url = database_url.replace(
        "?channel_binding=require",
        "",
    )

    database_url = database_url.replace(
        "&channel_binding=require",
        "",
    )

    database_url = database_url.replace(
        "?sslmode=require",
        "",
    )

    database_url = database_url.replace(
        "&sslmode=require",
        "",
    )

    connect_args["ssl"] = "require"


# ============================================================
# SQLALCHEMY ASYNC ENGINE
# ============================================================

engine = create_async_engine(
    database_url,
    echo=False,
    pool_pre_ping=True,
    connect_args=connect_args,
)


# ============================================================
# SESSION
# ============================================================

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
# DATABASE DEPENDENCY
# ============================================================

async def get_db():
    async with SessionLocal() as session:
        yield session


# ============================================================
# INITIALIZE DATABASE
# ============================================================

async def init_db():

    # Register SQLAlchemy models
    from models import db_models  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
