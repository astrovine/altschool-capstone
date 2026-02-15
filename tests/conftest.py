import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.utils.security import hash_pw, mint_token
from app.models.user import User
from app.models.course import Course
from app.models.enrollment import Enrollment

TEST_DB = "sqlite+aiosqlite://"

engine_test = create_async_engine(TEST_DB, echo=False)
TestSession = async_sessionmaker(bind=engine_test, class_=AsyncSession, expire_on_commit=False)


@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


async def _override_db():
    session = TestSession()
    try:
        yield session
    finally:
        await session.close()


app.dependency_overrides[get_db] = _override_db


@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest_asyncio.fixture
async def student_in_db():
    async with TestSession() as db:
        u = User(
            id="student-001",
            name="Jane Doe",
            email="jane@test.com",
            hashed_password=hash_pw("secret123"),
            role="student",
        )
        db.add(u)
        await db.commit()
        await db.refresh(u)
        return u


@pytest_asyncio.fixture
async def admin_in_db():
    async with TestSession() as db:
        u = User(
            id="admin-001",
            name="Admin Boss",
            email="admin@test.com",
            hashed_password=hash_pw("admin123"),
            role="admin",
        )
        db.add(u)
        await db.commit()
        await db.refresh(u)
        return u


@pytest_asyncio.fixture
async def inactive_user_in_db():
    async with TestSession() as db:
        u = User(
            id="inactive-001",
            name="Ghost",
            email="ghost@test.com",
            hashed_password=hash_pw("nope1234"),
            role="student",
            is_active=False,
        )
        db.add(u)
        await db.commit()
        return u


@pytest_asyncio.fixture
def student_token(student_in_db):
    return mint_token(student_in_db.id)


@pytest_asyncio.fixture
def admin_token(admin_in_db):
    return mint_token(admin_in_db.id)


def auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def sample_course():
    async with TestSession() as db:
        c = Course(id="course-001", title="Intro to Python", code="PY101", capacity=2)
        db.add(c)
        await db.commit()
        await db.refresh(c)
        return c


@pytest_asyncio.fixture
async def inactive_course():
    async with TestSession() as db:
        c = Course(id="course-inactive", title="Old Course", code="OLD99", capacity=5, is_active=False)
        db.add(c)
        await db.commit()
        return c


@pytest_asyncio.fixture
async def full_course(student_in_db):
    async with TestSession() as db:
        c = Course(id="course-full", title="Packed Room", code="FULL01", capacity=1)
        db.add(c)
        await db.flush()
        filler = User(id="filler-001", name="Filler", email="filler@test.com", hashed_password=hash_pw("fill1234"), role="student")
        db.add(filler)
        await db.flush()
        e = Enrollment(user_id=filler.id, course_id=c.id)
        db.add(e)
        await db.commit()
        return c
