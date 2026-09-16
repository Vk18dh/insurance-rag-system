import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.main import app
from backend.app.db.database import Base
from backend.app.dependencies.db import get_db

# Import models so Base metadata is populated
from backend.app.models.user import User
from backend.app.models.conversation import Conversation
from backend.app.models.message import Message
from backend.app.models.review_task import ReviewTask
from backend.app.models.document import Document
from backend.app.models.audit import SecurityAuditLog

from sqlalchemy.pool import StaticPool

from sqlalchemy import event

# Use an in-memory SQLite database for testing (or a file if WAL is needed, memory doesn't support WAL well)
# Actually, for multiple concurrent writers in tests, a file-based sqlite DB with WAL is best.
import os

test_db_url = os.environ.get("TEST_DATABASE_URL")
if test_db_url:
    SQLALCHEMY_DATABASE_URL = test_db_url
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
else:
    import tempfile
    test_db_file = tempfile.NamedTemporaryFile(delete=False)
    SQLALCHEMY_DATABASE_URL = f"sqlite:///{test_db_file.name}"

    engine = create_engine(
        SQLALCHEMY_DATABASE_URL, 
        connect_args={"check_same_thread": False, "timeout": 15},
        poolclass=StaticPool
    )

    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.close()

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

import unittest.mock as mock

class DummySession:
    def __init__(self, db):
        self.db = db
    def add(self, obj):
        self.db.add(obj)
    def commit(self):
        self.db.flush()
    def rollback(self):
        pass
    def close(self):
        pass

@pytest.fixture(scope="function")
def db_session():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    
    patcher = None
    if not test_db_url:
        # Globally patch AuditService to use the test db transaction ONLY for SQLite
        def fake_session():
            return DummySession(db)
            
        patcher = mock.patch("backend.app.services.audit_service.SessionLocal", new=fake_session)
        patcher.start()
    
    try:
        yield db
    finally:
        if patcher:
            patcher.stop()
        db.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()
