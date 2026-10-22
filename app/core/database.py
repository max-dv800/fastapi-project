from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import sessionmaker


from app.core.config import settings

engine = create_async_engine(
    url=settings.db_url,
    echo=True,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine, class_=AsyncSession, autoflush=False, expire_on_commit=False
)

engine_celery = create_engine(url=settings.db_url_sync, pool_pre_ping=True, pool_size=5, max_overflow=10)

SessionLocalCelery = sessionmaker(
    bind=engine_celery, autoflush=False, expire_on_commit=False
)


async def db_session():
    async with AsyncSessionLocal() as session:
            yield session

def db_celery_session():
    with SessionLocalCelery() as session:
            yield session