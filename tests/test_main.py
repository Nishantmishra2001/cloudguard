import pytest

from app.main import app, environments


@pytest.fixture
def client():
    environments.clear()

    with app.test_client() as client:
        yield client

    environments.clear()


def test_home(client):
    response = client.get("/")

    assert response.status_code == 200
    assert b"CloudGuard" in response.data
    assert b"Create Preview Environment" in response.data


def test_health(client):
    response = client.get("/health")

    assert response.status_code == 200

    data = response.get_json()

    assert data["status"] == "healthy"


def test_environment(client):
    response = client.get("/environment")

    assert response.status_code == 200

    data = response.get_json()

    assert data["environment"] == "preview"
    assert data["status"] == "active"


def test_list_environments_empty(client):
    response = client.get("/environments")

    assert response.status_code == 200

    data = response.get_json()

    assert data["count"] == 0
    assert data["environments"] == []


def test_create_environment(client):
    response = client.post(
        "/environments",
        json={
            "branch": "feature/login",
            "commit": "abc123",
            "ttl_minutes": 60
        }
    )

    assert response.status_code == 201

    data = response.get_json()

    assert data["environment"] == "preview"
    assert data["status"] == "active"
    assert data["branch"] == "feature/login"
    assert data["commit"] == "abc123"
    assert data["expires_in"] == "60 minutes"

    assert "id" in data
    assert "created_at" in data
    assert "expires_at" in data


def test_create_environment_defaults(client):
    response = client.post(
        "/environments",
        json={}
    )

    assert response.status_code == 201

    data = response.get_json()

    assert data["branch"] == "feature/demo"
    assert data["commit"] == "local-dev"
    assert data["expires_in"] == "60 minutes"


def test_invalid_ttl(client):
    response = client.post(
        "/environments",
        json={
            "ttl_minutes": 0
        }
    )

    assert response.status_code == 400


def test_delete_environment(client):
    create_response = client.post(
        "/environments",
        json={
            "branch": "feature/test",
            "commit": "xyz789",
            "ttl_minutes": 60
        }
    )

    environment_id = create_response.get_json()["id"]

    delete_response = client.delete(
        f"/environments/{environment_id}"
    )

    assert delete_response.status_code == 200

    data = delete_response.get_json()

    assert data["message"] == "Preview environment deleted"


def test_delete_missing_environment(client):
    response = client.delete(
        "/environments/not-found"
    )

    assert response.status_code == 404


def test_environment_list_after_create(client):
    client.post(
        "/environments",
        json={
            "branch": "feature/api",
            "commit": "commit123",
            "ttl_minutes": 30
        }
    )

    response = client.get("/environments")

    assert response.status_code == 200

    data = response.get_json()

    assert data["count"] == 1
    assert data["environments"][0]["branch"] == "feature/api"
