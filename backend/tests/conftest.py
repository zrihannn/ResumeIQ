import os
os.environ.setdefault("AUTO_CREATE_SCHEMA", "false")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.session import Base, get_db
from app.main import app
from app.core.config import settings


@pytest.fixture()
def client(tmp_path):
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    original_storage = settings.resume_storage_dir
    settings.resume_storage_dir = tmp_path / "resumes"
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        test_client.test_db = TestingSessionLocal
        yield test_client
    app.dependency_overrides.clear()
    settings.resume_storage_dir = original_storage
    Base.metadata.drop_all(bind=engine)
    engine.dispose()
