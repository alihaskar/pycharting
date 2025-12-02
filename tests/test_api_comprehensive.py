"""Comprehensive API testing including performance and workflow tests."""
import pytest
import time
from fastapi.testclient import TestClient
from src.api.main import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


def test_end_to_end_workflow(client, sample_ohlc_csv, setup_data_dir):
    """Test complete workflow: load, resample, calculate indicators."""
    # Step 1: Load basic data
    response = client.get(f"/chart-data?filename={sample_ohlc_csv.name}")
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) == 6  # OHLCV
    
    # Step 2: Add indicators
    response = client.get(
        f"/chart-data?filename={sample_ohlc_csv.name}&indicators=SMA:5"
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) == 7  # OHLCV + SMA
    
    # Step 3: Add resampling
    response = client.get(
        f"/chart-data?filename={sample_ohlc_csv.name}&timeframe=2h"
    )
    assert response.status_code == 200
    data = response.json()
    original_rows = 10
    resampled_rows = len(data["data"][0])
    assert resampled_rows < original_rows
    
    # Step 4: Combine all features
    response = client.get(
        f"/chart-data?filename={sample_ohlc_csv.name}"
        "&indicators=RSI:14&indicators=SMA:5&indicators=EMA:12"
        "&timeframe=2h"
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) == 9  # OHLCV + 3 indicators


def test_performance_small_dataset(client, sample_ohlc_csv, setup_data_dir):
    """Test API performance with small dataset."""
    start_time = time.time()
    
    response = client.get(f"/chart-data?filename={sample_ohlc_csv.name}")
    
    elapsed = time.time() - start_time
    
    assert response.status_code == 200
    # Should be very fast for small dataset
    assert elapsed < 1.0


def test_performance_large_dataset(client, large_ohlc_csv, setup_data_dir):
    """Test API performance with large dataset (1000 rows)."""
    start_time = time.time()
    
    response = client.get(f"/chart-data?filename={large_ohlc_csv.name}")
    
    elapsed = time.time() - start_time
    
    assert response.status_code == 200
    # Should complete within reasonable time
    assert elapsed < 5.0


def test_performance_with_indicators(client, large_ohlc_csv, setup_data_dir):
    """Test API performance with multiple indicators on large dataset."""
    start_time = time.time()
    
    response = client.get(
        f"/chart-data?filename={large_ohlc_csv.name}"
        "&indicators=RSI:14&indicators=SMA:20&indicators=EMA:12"
    )
    
    elapsed = time.time() - start_time
    
    assert response.status_code == 200
    # Should still be reasonably fast
    assert elapsed < 5.0


def test_data_consistency_across_requests(client, sample_ohlc_csv, setup_data_dir):
    """Test that same request returns consistent data."""
    # Make same request twice
    response1 = client.get(f"/chart-data?filename={sample_ohlc_csv.name}")
    response2 = client.get(f"/chart-data?filename={sample_ohlc_csv.name}")
    
    assert response1.status_code == 200
    assert response2.status_code == 200
    
    # Should return identical data
    assert response1.json() == response2.json()


def test_handles_missing_values_gracefully(client, csv_with_nans, setup_data_dir):
    """Test that missing values are handled without errors."""
    response = client.get(f"/chart-data?filename={csv_with_nans.name}")
    
    assert response.status_code == 200
    data = response.json()
    
    # Should have data (missing values are filled by clean_missing_values)
    assert len(data["data"]) == 6
    
    # Data should be complete (no None after cleaning)
    # Our clean_missing_values uses forward-fill for prices
    assert data["data"][0] is not None  # timestamps
    assert len(data["data"][1]) == 4  # open column exists


def test_handles_time_gaps(client, csv_with_gaps, setup_data_dir):
    """Test that time gaps in data are handled."""
    response = client.get(f"/chart-data?filename={csv_with_gaps.name}")
    
    assert response.status_code == 200
    data = response.json()
    
    # Should return data despite gaps
    assert len(data["data"][0]) == 4


def test_indicator_calculation_accuracy(client, sample_ohlc_csv, setup_data_dir):
    """Test that indicators are calculated correctly."""
    response = client.get(
        f"/chart-data?filename={sample_ohlc_csv.name}&indicators=SMA:3"
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Verify SMA is in response
    assert len(data["data"]) == 7
    
    # SMA should have NaN for first 2 values (period-1)
    sma_values = data["data"][6]
    assert sma_values[0] is None
    assert sma_values[1] is None
    # Third value should be average of first 3 closes
    # closes: 102, 104, 106 -> SMA = 104
    assert sma_values[2] == pytest.approx(104.0, abs=0.1)


def test_resampling_accuracy(client, sample_ohlc_csv, setup_data_dir):
    """Test that resampling aggregates correctly."""
    response = client.get(
        f"/chart-data?filename={sample_ohlc_csv.name}&timeframe=5h"
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # 10 hours / 5 = 2 bars
    timestamps = data["data"][0]
    assert len(timestamps) <= 3  # Allow for bin alignment


def test_metadata_completeness(client, sample_ohlc_csv, setup_data_dir):
    """Test that metadata contains all expected fields."""
    response = client.get(
        f"/chart-data?filename={sample_ohlc_csv.name}"
        "&indicators=RSI:14&timeframe=2h"
    )
    
    assert response.status_code == 200
    metadata = response.json()["metadata"]
    
    # Check all expected fields
    assert "filename" in metadata
    assert "rows" in metadata
    assert "columns" in metadata
    assert "timeframe" in metadata
    assert "indicators" in metadata
    
    # Verify values
    assert metadata["filename"] == sample_ohlc_csv.name
    assert metadata["rows"] > 0
    assert metadata["columns"] >= 6
    assert metadata["timeframe"] == "2h"


def test_concurrent_requests(client, sample_ohlc_csv, setup_data_dir):
    """Test that API handles multiple concurrent requests."""
    import concurrent.futures
    
    def make_request():
        return client.get(f"/chart-data?filename={sample_ohlc_csv.name}")
    
    # Make 10 concurrent requests
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(make_request) for _ in range(10)]
        results = [f.result() for f in futures]
    
    # All should succeed
    assert all(r.status_code == 200 for r in results)
    
    # All should return same data
    first_data = results[0].json()
    for result in results[1:]:
        assert result.json() == first_data


def test_response_headers(client, sample_ohlc_csv, setup_data_dir):
    """Test that response headers are set correctly."""
    response = client.get(
        f"/chart-data?filename={sample_ohlc_csv.name}",
        headers={"Origin": "http://localhost:3000"}
    )
    
    assert response.status_code == 200
    
    # Check content-type
    assert "application/json" in response.headers["content-type"]
    
    # Check CORS headers (present when Origin header sent)
    assert "access-control-allow-origin" in response.headers


def test_empty_indicators_list(client, sample_ohlc_csv, setup_data_dir):
    """Test that empty indicators list works correctly."""
    response = client.get(
        f"/chart-data?filename={sample_ohlc_csv.name}&indicators="
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Should just return OHLCV
    assert len(data["data"]) == 6

