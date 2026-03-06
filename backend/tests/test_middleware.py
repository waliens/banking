"""Tests for the error logging middleware in main.py."""


class TestMiddleware:
    def test_health_endpoint_returns_200(self, client):
        r = client.get("/api/v2/health")
        assert r.status_code == 200
        assert r.json() == {"status": "ok"}

    def test_non_existent_endpoint_returns_404(self, client):
        r = client.get("/api/v2/does-not-exist")
        assert r.status_code == 404

    def test_404_response_has_detail(self, client):
        r = client.get("/api/v2/nonexistent-route")
        assert r.status_code == 404
        assert "detail" in r.json()
