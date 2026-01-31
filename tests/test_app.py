"""Tests for the CloudScope FastAPI application."""


def test_health(client):
    """Test /health returns 200 and includes services."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "services" in data
    assert "timestamp" in data


def test_health_services(client):
    """Test /health includes database and cache in services."""
    response = client.get("/health")
    assert response.status_code == 200
    services = response.json().get("services", {})
    assert "database" in services
    assert "cache" in services


def test_api_docs(client):
    """Test OpenAPI docs are served."""
    response = client.get("/api/docs")
    assert response.status_code == 200


def test_api_openapi_json(client):
    """Test OpenAPI schema is served."""
    response = client.get("/api/openapi.json")
    assert response.status_code == 200
    data = response.json()
    assert "openapi" in data
    assert "paths" in data


def test_resources_no_profile(client):
    """Test /api/resources returns 400 when no active profile."""
    response = client.get("/api/resources")
    assert response.status_code == 400
    assert "detail" in response.json()


def test_resources_refresh_no_profile(client):
    """Test POST /api/resources/refresh returns 400 when no active profile."""
    response = client.post("/api/resources/refresh")
    assert response.status_code == 400
    assert "detail" in response.json()


def test_404(client):
    """Test 404 for unknown path."""
    response = client.get("/nonexistent")
    assert response.status_code == 404
