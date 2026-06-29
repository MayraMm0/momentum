# "client" param on each func -> pytest matches it to the client ficture in conftest.py
# and injects a fresh TestClient (empty in-memory DB, tests can't see each others data)


def test_register_creates_user_and_excludes_password(client):
    response = client.post("/register", json={
        "username": "jose",
        "email": "jose@example.com",
        "password": "supersecret123",
    })
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "jose"
    assert data["email"] == "jose@example.com"
    assert "password" not in data
    assert "password_hash" not in data


def test_register_duplicate_username_fails(client):
    client.post("/register", json={
        "username": "jose",
        "email": "jose@example.com",
        "password": "supersecret123",
    })
    response = client.post("/register", json={
        "username": "jose",
        "email": "different@example.com",
        "password": "anotherpassword",
    })
    assert response.status_code == 400


def test_login_with_correct_credentials_returns_token(client):
    client.post("/register", json={
        "username": "may",
        "email": "may@example.com",
        "password": "mypassword123",
    })
    response = client.post("/login", json={
        "username": "may",
        "password": "mypassword123",
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_with_wrong_password_fails(client):
    client.post("/register", json={
        "username": "may",
        "email": "may@example.com",
        "password": "mypassword456",
    })
    response = client.post("/login", json={
        "username": "may",
        "password": "wrongpassword",
    })
    assert response.status_code == 401