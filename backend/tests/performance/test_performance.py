"""
Phase 6 performance tests.
"""

import time


def test_health_endpoint_under_500ms(api_client):
    start = time.perf_counter()
    resp = api_client.get("/health")
    elapsed = (time.perf_counter() - start) * 1000
    assert resp.status_code == 200
    assert elapsed < 500.0, f"/health too slow: {elapsed:.2f}ms"


def test_root_endpoint_under_500ms(api_client):
    start = time.perf_counter()
    resp = api_client.get("/")
    elapsed = (time.perf_counter() - start) * 1000
    assert resp.status_code == 200
    assert elapsed < 500.0, f"/ too slow: {elapsed:.2f}ms"
