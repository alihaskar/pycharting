"""Stress tests for the session registry and the slicing path under concurrency.

``_data_managers`` is a plain module-level dict shared by every request handler,
and the chart frontend issues overlapping ``/api/data`` requests while the user
pans. These tests push that path harder than the unit suite does: many sessions
at once, churn of create/delete, and concurrent reads of the same manager.

Run with ``make stress``. Excluded from ``make test``.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor

import numpy as np
import pytest
from fastapi.testclient import TestClient

from pycharting.api.routes import _data_managers
from pycharting.core.server import create_app
from pycharting.data.ingestion import DataManager

pytestmark = pytest.mark.stress

BARS = 20_000
SESSIONS = 100
WORKERS = 16


@pytest.fixture
def client() -> TestClient:
    """A test client over a fresh app, with the session registry cleared around it."""
    _data_managers.clear()
    try:
        yield TestClient(create_app())
    finally:
        _data_managers.clear()


def _series(n: int = BARS) -> dict[str, np.ndarray]:
    """A deterministic OHLC payload of ``n`` bars."""
    rng = np.random.default_rng(seed=1)
    close = np.cumsum(rng.standard_normal(n)) + 500.0
    return {
        "index": np.arange(n),
        "open": close - 0.5,
        "high": close + 1.0,
        "low": close - 1.0,
        "close": close,
    }


def test_many_concurrent_sessions_stay_isolated(client: TestClient) -> None:
    """Registering many sessions at once keeps each one's data distinct."""
    payload = _series(1_000)

    def register(i: int) -> str:
        # Shift the whole bar, not just close — validate_input enforces
        # high >= max(open, close), so offsetting one series in isolation
        # is rejected.
        session = f"stress-{i}"
        shifted = {k: (v + i if k != "index" else v) for k, v in payload.items()}
        _data_managers[session] = DataManager(**shifted)
        return session

    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        sessions = list(pool.map(register, range(SESSIONS)))

    assert len(_data_managers) == SESSIONS
    # Each session kept its own offset rather than aliasing a shared array.
    for i, session in enumerate(sessions):
        assert _data_managers[session].close[0] == pytest.approx(payload["close"][0] + i)


def test_concurrent_chunk_reads_are_consistent(client: TestClient) -> None:
    """Overlapping viewport reads of one session all return the same bytes."""
    _data_managers["shared"] = DataManager(**_series())
    manager = _data_managers["shared"]
    expected = manager.get_chunk(0, 500)["close"]

    def read(_: int) -> list[float]:
        return manager.get_chunk(0, 500)["close"]

    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        results = list(pool.map(read, range(200)))

    assert all(r == expected for r in results)


def test_session_churn_does_not_leak(client: TestClient) -> None:
    """Repeated create/delete cycles leave the registry empty."""
    for i in range(SESSIONS):
        session = f"churn-{i}"
        _data_managers[session] = DataManager(**_series(500))
        response = client.delete(f"/api/sessions/{session}")
        assert response.status_code == 200

    assert _data_managers == {}


def test_full_range_slice_of_a_large_series(client: TestClient) -> None:
    """A whole-series slice serializes every bar without truncating."""
    _data_managers["big"] = DataManager(**_series())

    chunk = _data_managers["big"].get_chunk()

    assert len(chunk["index"]) == BARS
    assert len(chunk["close"]) == BARS
