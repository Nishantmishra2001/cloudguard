from app.main import app


def test_home():
    client = app.test_client()

    response = client.get("/")

    assert response.status_code == 200

    data = response.get_json()

    assert data["project"] == "CloudGuard"
    assert data["status"] == "running"


def test_health():
    client = app.test_client()

    response = client.get("/health")

    assert response.status_code == 200

    data = response.get_json()

    assert data["status"] == "healthy"


def test_environment():
    client = app.test_client()

    response = client.get("/environment")

    assert response.status_code == 200

    data = response.get_json()

    assert data["environment"] == "preview"
    assert data["status"] == "active"
