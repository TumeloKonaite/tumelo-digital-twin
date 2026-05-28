from __future__ import annotations


def test_health_route_returns_healthy_status(client) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}
