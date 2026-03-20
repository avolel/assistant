import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
from assistant.api.app import app
 
client = TestClient(app) # Create a test client for the FastAPI app to simulate API requests.

# Test that the health check endpoint returns a 200 status and the expected JSON response. 
def test_health_check():
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"

# Test that the identity endpoint returns the correct structure when no identity is configured. 
def test_get_identity_unconfigured(fresh_db):
    r = client.get("/api/identity/")
    assert r.status_code == 200
    assert r.json()["configured"] is False