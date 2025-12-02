"""Integration tests for API with data processing modules."""
import pytest
from fastapi.testclient import TestClient
from src.api.main import app
import os
from pathlib import Path


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def sample_csv(tmp_path):
    """Create a sample CSV file for testing."""
    csv_content = """timestamp,open,high,low,close,volume
2024-01-01 09:00:00,100.0,105.0,95.0,102.0,1000
2024-01-01 10:00:00,102.0,106.0,98.0,104.0,1100
2024-01-01 11:00:00,104.0,108.0,100.0,106.0,1200
2024-01-01 12:00:00,106.0,110.0,102.0,108.0,1300
2024-01-01 13:00:00,108.0,112.0,104.0,110.0,1400
"""
    csv_file = tmp_path / "test_data.csv"
    csv_file.write_text(csv_content)
    return csv_file


def test_chart_data_loads_csv(client, sample_csv, monkeypatch):
    """Test that endpoint loads CSV file correctly."""
    # Mock the data directory to point to test file
    monkeypatch.setenv("DATA_DIR", str(sample_csv.parent))
    
    response = client.get(f"/chart-data?filename={sample_csv.name}")
    
    assert response.status_code == 200
    data = response.json()
    
    # Verify response structure
    assert "data" in data
    assert "metadata" in data
    
    # Verify data is array of arrays
    assert isinstance(data["data"], list)
    assert len(data["data"]) > 0  # Should have columns


def test_chart_data_returns_uplot_format(client, sample_csv, monkeypatch):
    """Test that response is in uPlot columnar format."""
    monkeypatch.setenv("DATA_DIR", str(sample_csv.parent))
    
    response = client.get(f"/chart-data?filename={sample_csv.name}")
    
    assert response.status_code == 200
    data = response.json()["data"]
    
    # Should have 6 columns: timestamp + OHLCV
    assert len(data) == 6
    
    # All columns should have same length
    lengths = [len(col) for col in data]
    assert len(set(lengths)) == 1
    
    # Should have 5 data points
    assert lengths[0] == 5


def test_chart_data_with_indicators(client, sample_csv, monkeypatch):
    """Test that indicators are calculated and included."""
    monkeypatch.setenv("DATA_DIR", str(sample_csv.parent))
    
    response = client.get(
        f"/chart-data?filename={sample_csv.name}&indicators=RSI:14&indicators=SMA:20"
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Should have OHLCV + indicators
    assert len(data["data"]) > 6
    
    # Metadata should list indicators
    assert "indicators" in data["metadata"]
    assert len(data["metadata"]["indicators"]) > 0


def test_chart_data_with_resampling(client, sample_csv, monkeypatch):
    """Test that timeframe resampling works."""
    monkeypatch.setenv("DATA_DIR", str(sample_csv.parent))
    
    response = client.get(
        f"/chart-data?filename={sample_csv.name}&timeframe=2h"
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Should resample 5 hours of data into fewer bars
    row_count = len(data["data"][0])
    assert row_count < 5  # Should be less than original


def test_chart_data_timestamps_are_unix(client, sample_csv, monkeypatch):
    """Test that timestamps are Unix milliseconds."""
    monkeypatch.setenv("DATA_DIR", str(sample_csv.parent))
    
    response = client.get(f"/chart-data?filename={sample_csv.name}")
    
    assert response.status_code == 200
    timestamps = response.json()["data"][0]
    
    # Should be Unix timestamps (integers)
    assert all(isinstance(ts, int) for ts in timestamps)
    
    # Should be in milliseconds (13 digits for 2024)
    assert all(len(str(ts)) == 13 for ts in timestamps)


def test_chart_data_file_not_found(client):
    """Test error handling for non-existent file."""
    response = client.get("/chart-data?filename=nonexistent.csv")
    
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_chart_data_metadata_accurate(client, sample_csv, monkeypatch):
    """Test that metadata reflects actual data."""
    monkeypatch.setenv("DATA_DIR", str(sample_csv.parent))
    
    response = client.get(f"/chart-data?filename={sample_csv.name}")
    
    assert response.status_code == 200
    metadata = response.json()["metadata"]
    
    # Should have accurate counts
    assert metadata["rows"] == 5
    assert metadata["columns"] == 6
    assert metadata["filename"] == sample_csv.name


def test_chart_data_preserves_ohlc_relationships(client, sample_csv, monkeypatch):
    """Test that OHLC relationships are maintained."""
    monkeypatch.setenv("DATA_DIR", str(sample_csv.parent))
    
    response = client.get(f"/chart-data?filename={sample_csv.name}")
    
    assert response.status_code == 200
    data = response.json()["data"]
    
    # Extract OHLC
    opens = data[1]
    highs = data[2]
    lows = data[3]
    closes = data[4]
    
    # Verify relationships for each bar
    for i in range(len(opens)):
        assert highs[i] >= opens[i], f"High {highs[i]} < Open {opens[i]}"
        assert highs[i] >= closes[i], f"High {highs[i]} < Close {closes[i]}"
        assert lows[i] <= opens[i], f"Low {lows[i]} > Open {opens[i]}"
        assert lows[i] <= closes[i], f"Low {lows[i]} > Close {closes[i]}"


def test_chart_data_chronological_order(client, sample_csv, monkeypatch):
    """Test that data is in chronological order."""
    monkeypatch.setenv("DATA_DIR", str(sample_csv.parent))
    
    response = client.get(f"/chart-data?filename={sample_csv.name}")
    
    assert response.status_code == 200
    timestamps = response.json()["data"][0]
    
    # Should be in ascending order
    assert timestamps == sorted(timestamps)


def test_chart_data_handles_nan_values(client, tmp_path, monkeypatch):
    """Test that NaN values are handled correctly."""
    csv_content = """timestamp,open,high,low,close,volume
2024-01-01 09:00:00,100.0,105.0,95.0,102.0,1000
2024-01-01 10:00:00,,106.0,98.0,104.0,1100
2024-01-01 11:00:00,104.0,108.0,100.0,106.0,
"""
    csv_file = tmp_path / "nan_data.csv"
    csv_file.write_text(csv_content)
    
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    
    response = client.get(f"/chart-data?filename={csv_file.name}")
    
    assert response.status_code == 200
    data = response.json()["data"]
    
    # NaN should be converted to null (None in Python, null in JSON)
    # Check that data structure is maintained
    assert len(data) == 6


def test_chart_data_multiple_indicators(client, sample_csv, monkeypatch):
    """Test multiple indicators with different parameters."""
    monkeypatch.setenv("DATA_DIR", str(sample_csv.parent))
    
    response = client.get(
        f"/chart-data?filename={sample_csv.name}"
        "&indicators=RSI:14&indicators=SMA:10&indicators=EMA:12"
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Should have OHLCV (6) + 3 indicators = 9 columns
    assert len(data["data"]) == 9
    
    # Metadata should list all indicators
    assert len(data["metadata"]["indicators"]) == 3

