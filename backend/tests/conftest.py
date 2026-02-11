"""테스트 픽스처 및 공통 설정.

SQLite in-memory async 엔진을 사용한 테스트 환경을 구성합니다.
"""
import asyncio
import pytest
import pytest_asyncio
from uuid import uuid4
from datetime import datetime
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.database import Base, get_db
from app.main import app
from app.models.user import User
from app.models.company import Company, CompanyMember, MemberRole
from app.models.reminder import Reminder
from app.services.template_engine import seed_system_templates
from app.utils.security import hash_password, create_access_token


# SQLite async engine for tests
TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def engine():
    eng = create_async_engine(TEST_DB_URL, echo=False)
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield eng
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await eng.dispose()


@pytest_asyncio.fixture
async def db_session(engine):
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def client(engine):
    """FastAPI 테스트 클라이언트. DB를 테스트용 SQLite로 오버라이드합니다."""
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async def override_get_db():
        async with session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    app.dependency_overrides[get_db] = override_get_db

    # Seed system templates
    async with session_factory() as seed_session:
        await seed_system_templates(seed_session)
        await seed_session.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession) -> User:
    """테스트 사용자를 생성합니다."""
    user = User(
        id=uuid4(),
        email="test@example.com",
        password_hash=hash_password("password123"),
        name="테스트유저",
        is_active=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def test_company(db_session: AsyncSession, test_user: User) -> Company:
    """테스트 회사를 생성합니다."""
    company = Company(
        id=uuid4(),
        name="테스트 회사",
        business_number="123-45-67890",
        owner_id=test_user.id,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db_session.add(company)
    await db_session.flush()

    member = CompanyMember(
        id=uuid4(),
        company_id=company.id,
        user_id=test_user.id,
        role=MemberRole.OWNER,
        joined_at=datetime.utcnow(),
    )
    db_session.add(member)
    await db_session.commit()
    await db_session.refresh(company)
    return company


@pytest_asyncio.fixture
def auth_headers(test_user: User) -> dict:
    """인증 헤더를 생성합니다."""
    token = create_access_token(test_user.id)
    return {"Authorization": f"Bearer {token}"}
