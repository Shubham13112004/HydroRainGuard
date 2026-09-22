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

# Convert PostgreSQL URL to asyncpg URL
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
# NEON / ASYNCPG SSL
# ============================================================

connect_args = {}

if database_url.startswith("postgresql+asyncpg://"):

    # SQLAlchemy's sslmode parameter is not passed directly
    # to asyncpg. Remove it and provide SSL through connect_args.
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
# ASYNC SQLALCHEMY ENGINE
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

    # Import models so SQLAlchemy registers Assessment
    from models import db_models  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
