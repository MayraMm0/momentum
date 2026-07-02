# Special filename - fixtures defined here are automatically available to every file in tests/
# no imports needed

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from backend.database import Base, get_db
from backend.main import app

# In-memory SQLite - speed (RAM), exists only for the test process, auto cleanup
TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args = {"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture()
def db_session():
    Base.metadata.create_all(bind = engine) # build all the tables
    session = TestingSessionLocal()
    
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind = engine) # wipe everything after the test
        
@pytest.fixture()
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass # db_session fixture handles closing
        
    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()
    
@pytest.fixture()
def auth_headers(client):
    # create a test user and log in to get an access token
    client.post("/register", json={
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpassword123",
    })
    
    response = client.post("/login", json={
        "username": "testuser",
        "password": "testpassword123",
    })
    
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}