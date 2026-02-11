from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.config import settings


class Base(DeclarativeBase):
    pass


def _create_engine():
    return create_async_engine(settings.DATABASE_URL, echo=settings.DEBUG)


def _create_session_factory(eng):
    return async_sessionmaker(eng, class_=AsyncSession, expire_on_commit=False)


# Lazy initialization to avoid import-time errors when asyncpg is not installed
_engine = None
_session_factory = None


def get_engine():
    global _engine
    if _engine is None:
        _engine = _create_engine()
    return _engine


def get_session_factory():
    global _session_factory
    if _session_factory is None:
        _session_factory = _create_session_factory(get_engine())
    return _session_factory


async def get_db() -> AsyncSession:
    factory = get_session_factory()
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
