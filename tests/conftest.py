"""Shared pytest fixtures for API testing."""
import pytest
from pathlib import Path
from fastapi.testclient import TestClient
from src.api.main import app


@pytest.fixture
def api_client():
    """
    Create FastAPI test client.
    
    Returns:
        TestClient instance for API testing
    """
    return TestClient(app)


@pytest.fixture
def sample_ohlc_csv(tmp_path):
    """
    Create a sample OHLC CSV file for testing.
    
    Args:
        tmp_path: pytest temporary directory
        
    Returns:
        Path to created CSV file
    """
    csv_content = """timestamp,open,high,low,close,volume
2024-01-01 09:00:00,100.0,105.0,95.0,102.0,1000
2024-01-01 10:00:00,102.0,106.0,98.0,104.0,1100
2024-01-01 11:00:00,104.0,108.0,100.0,106.0,1200
2024-01-01 12:00:00,106.0,110.0,102.0,108.0,1300
2024-01-01 13:00:00,108.0,112.0,104.0,110.0,1400
2024-01-01 14:00:00,110.0,114.0,106.0,112.0,1500
2024-01-01 15:00:00,112.0,116.0,108.0,114.0,1600
2024-01-01 16:00:00,114.0,118.0,110.0,116.0,1700
2024-01-01 17:00:00,116.0,120.0,112.0,118.0,1800
2024-01-01 18:00:00,118.0,122.0,114.0,120.0,1900
"""
    csv_file = tmp_path / "sample.csv"
    csv_file.write_text(csv_content)
    return csv_file


@pytest.fixture
def large_ohlc_csv(tmp_path):
    """
    Create a large OHLC CSV file for performance testing.
    
    Args:
        tmp_path: pytest temporary directory
        
    Returns:
        Path to created CSV file with 1000 rows
    """
    import pandas as pd
    import numpy as np
    
    # Generate 1000 rows of data
    dates = pd.date_range("2024-01-01", periods=1000, freq="1min")
    df = pd.DataFrame({
        "timestamp": dates,
        "open": np.random.uniform(100, 110, 1000),
        "high": np.random.uniform(110, 120, 1000),
        "low": np.random.uniform(90, 100, 1000),
        "close": np.random.uniform(100, 110, 1000),
        "volume": np.random.randint(1000, 2000, 1000)
    })
    
    csv_file = tmp_path / "large_data.csv"
    df.to_csv(csv_file, index=False)
    return csv_file


@pytest.fixture
def csv_with_gaps(tmp_path):
    """
    Create CSV with missing timestamps (gaps).
    
    Args:
        tmp_path: pytest temporary directory
        
    Returns:
        Path to created CSV file with time gaps
    """
    csv_content = """timestamp,open,high,low,close,volume
2024-01-01 09:00:00,100.0,105.0,95.0,102.0,1000
2024-01-01 10:00:00,102.0,106.0,98.0,104.0,1100
2024-01-01 13:00:00,104.0,108.0,100.0,106.0,1200
2024-01-01 14:00:00,106.0,110.0,102.0,108.0,1300
"""
    csv_file = tmp_path / "gaps.csv"
    csv_file.write_text(csv_content)
    return csv_file


@pytest.fixture
def csv_with_nans(tmp_path):
    """
    Create CSV with missing values (NaN).
    
    Args:
        tmp_path: pytest temporary directory
        
    Returns:
        Path to created CSV file with NaN values
    """
    csv_content = """timestamp,open,high,low,close,volume
2024-01-01 09:00:00,100.0,105.0,95.0,102.0,1000
2024-01-01 10:00:00,,106.0,98.0,104.0,1100
2024-01-01 11:00:00,104.0,108.0,100.0,106.0,
2024-01-01 12:00:00,106.0,110.0,102.0,,1300
"""
    csv_file = tmp_path / "nans.csv"
    csv_file.write_text(csv_content)
    return csv_file


@pytest.fixture
def setup_data_dir(tmp_path, monkeypatch):
    """
    Setup DATA_DIR environment variable for testing.
    
    Args:
        tmp_path: pytest temporary directory
        monkeypatch: pytest monkeypatch fixture
        
    Returns:
        Path to data directory
    """
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    return tmp_path

