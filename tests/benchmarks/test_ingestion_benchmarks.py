"""Benchmarks for the hot path: validation on ingest, and slicing on every viewport move.

``DataManager.get_chunk`` is called once per pan/zoom in the browser, so its cost
is what the user feels as lag. ``validate_input`` is paid once per ``plot()`` call
but walks every series, so it dominates start-up on large inputs.

Run with ``make benchmark``. These are excluded from ``make test``.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from pycharting.data.ingestion import DataManager, validate_input

# Large enough to be dominated by the array work rather than call overhead,
# small enough that the suite stays inside pytest.ini's 60s timeout.
N = 250_000
CHUNK = 5_000


@pytest.fixture(scope="module")
def ohlc() -> dict[str, np.ndarray]:
    """A dense OHLC series of ``N`` bars with a datetime index and two overlays."""
    rng = np.random.default_rng(seed=0)
    close = np.cumsum(rng.standard_normal(N)) + 1_000.0
    return {
        "index": pd.date_range("2020-01-01", periods=N, freq="min"),
        "open": close - 0.5,
        "high": close + 1.0,
        "low": close - 1.0,
        "close": close,
    }


@pytest.fixture(scope="module")
def manager(ohlc: dict[str, np.ndarray]) -> DataManager:
    """A ``DataManager`` over the dense series, built once for the module."""
    return DataManager(**ohlc)


def test_validate_input_on_dense_ohlc(benchmark, ohlc: dict[str, np.ndarray]) -> None:
    """Cost of normalizing a dense OHLC series — paid once per plot() call."""
    result = benchmark(lambda: validate_input(**ohlc))
    assert len(result["close"]) == N


def test_get_chunk_viewport_slice(benchmark, manager: DataManager) -> None:
    """Cost of one viewport slice — paid on every pan and zoom."""
    mid = N // 2
    result = benchmark(lambda: manager.get_chunk(mid, mid + CHUNK))
    assert len(result["index"]) == CHUNK


def test_get_chunk_full_range(benchmark, manager: DataManager) -> None:
    """Cost of serializing the whole series, the worst case on first paint."""
    result = benchmark(lambda: manager.get_chunk())
    assert len(result["index"]) == N


def test_data_manager_construction(benchmark, ohlc: dict[str, np.ndarray]) -> None:
    """End-to-end ingest cost: validation plus array retention."""
    result = benchmark(lambda: DataManager(**ohlc))
    assert result.length == N
