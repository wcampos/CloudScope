"""Test configuration and fixtures for FastAPI API."""

import os
import sys

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Ensure api (app) is on path: Docker uses /app, CI uses repo/api
_tests_dir = os.path.dirname(os.path.abspath(__file__))
_root = os.path.dirname(_tests_dir)
_api_dir = os.path.join(_root, "api")
if os.path.isdir(_api_dir) and os.path.isfile(os.path.join(_api_dir, "main.py")):
    sys.path.insert(0, _api_dir)
else:
    sys.path.insert(0, _root)

from database import Base, get_db  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from main import app  # noqa: E402

# In-memory SQLite for tests (no profiles)
TEST_ENGINE = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=TEST_ENGINE)


def override_get_db():
    """Yield a test DB session with empty tables (no active profile)."""
    Base.metadata.create_all(bind=TEST_ENGINE)
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def client():
    """FastAPI test client with test DB (no profiles)."""
    app.dependency_overrides[get_db] = override_get_db
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


@pytest.fixture
def aws_profile():
    """Minimal AWS profile-like object for AWS service class tests (no DB)."""
    from models import AWSProfile

    return AWSProfile(
        name="test-profile",
        aws_access_key_id="test-key",
        aws_secret_access_key="test-secret",
        aws_region="us-east-1",
        is_active=True,
    )


@pytest.fixture(autouse=True)
def setup_test_env():
    """Set test environment variables."""
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_DEFAULT_REGION"] = "us-east-1"
    yield
