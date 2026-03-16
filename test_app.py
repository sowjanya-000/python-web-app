import pytest
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from app import app as flask_app, db

@pytest.fixture
def client():
    flask_app.config["TESTING"] = True
    flask_app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    flask_app.config["SECRET_KEY"] = "test-secret"
    with flask_app.app_context():
        db.create_all()
        yield flask_app.test_client()
        db.drop_all()

def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.get_json()["status"] == "healthy"

def test_register(client):
    r = client.post("/api/register", json={
        "username": "testuser", "email": "test@example.com", "password": "secret123"
    })
    assert r.status_code == 201

def test_login(client):
    client.post("/api/register", json={
        "username": "testuser", "email": "test@example.com", "password": "secret123"
    })
    r = client.post("/api/login", json={"email": "test@example.com", "password": "secret123"})
    assert r.status_code == 200

def test_login_wrong_password(client):
    client.post("/api/register", json={
        "username": "testuser", "email": "test@example.com", "password": "secret123"
    })
    r = client.post("/api/login", json={"email": "test@example.com", "password": "wrongpass"})
    assert r.status_code == 401

def test_create_task(client):
    client.post("/api/register", json={
        "username": "testuser", "email": "test@example.com", "password": "secret123"
    })
    r = client.post("/api/tasks", json={"title": "My first task", "priority": "high"})
    assert r.status_code == 201
    assert r.get_json()["title"] == "My first task"

def test_get_tasks(client):
    client.post("/api/register", json={
        "username": "testuser", "email": "test@example.com", "password": "secret123"
    })
    client.post("/api/tasks", json={"title": "Task A"})
    client.post("/api/tasks", json={"title": "Task B"})
    r = client.get("/api/tasks")
    assert r.status_code == 200
    assert len(r.get_json()) == 2

def test_update_task(client):
    client.post("/api/register", json={
        "username": "testuser", "email": "test@example.com", "password": "secret123"
    })
    t = client.post("/api/tasks", json={"title": "Task"}).get_json()
    r = client.patch(f"/api/tasks/{t['id']}", json={"status": "done"})
    assert r.status_code == 200

def test_delete_task(client):
    client.post("/api/register", json={
        "username": "testuser", "email": "test@example.com", "password": "secret123"
    })
    t = client.post("/api/tasks", json={"title": "Task"}).get_json()
    r = client.delete(f"/api/tasks/{t['id']}")
    assert r.status_code == 200
    assert len(client.get("/api/tasks").get_json()) == 0

def test_unauthorized(client):
    r = client.get("/api/tasks")
    assert r.status_code == 401
