"""
Pytest fixtures for testing
"""
import sys
from pathlib import Path
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

# Add backend directory to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

# Mock CodeAnalyzer to avoid tree-sitter import issues in test environment
with patch('app.services.code_analyzer.CodeAnalyzer', MagicMock()):
    from app.main import app
    from app.models.base import Base
    from app.models.user import User, UserRole
    from app.core.database import get_db


@pytest.fixture(scope="function")
def engine():
    """Create in-memory SQLite database for testing"""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session(engine):
    """Create database session for testing"""
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(db_session):
    """Create FastAPI test client with test database"""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def sample_user(db_session) -> User:
    """Create a sample user for testing"""
    user = User(
        name="Test User",
        email="test@lab.com",
        github_username="test_user",
        role=UserRole.STUDENT
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user
