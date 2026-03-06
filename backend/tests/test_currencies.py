"""Tests for currency endpoints."""


class TestListCurrencies:
    def test_list_currencies(self, client, auth_headers, currency_eur):
        r = client.get("/api/v2/currencies", headers=auth_headers)
        assert r.status_code == 200
        data = r.json()
        assert len(data) == 1
        assert data[0]["short_name"] == "EUR"
        assert data[0]["symbol"] == "€"

    def test_list_unauthenticated(self, client):
        r = client.get("/api/v2/currencies")
        assert r.status_code == 401
