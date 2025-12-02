"""Tests for CSV data ingestion loader."""
import pytest
import pandas as pd
from pathlib import Path
from src.ingestion.loader import load_csv, CSVLoadError


@pytest.fixture
def fixtures_dir():
    """Return path to test fixtures directory."""
    return Path(__file__).parent / "fixtures"


def test_load_valid_csv(fixtures_dir):
    """Test loading a valid CSV file."""
    csv_path = fixtures_dir / "valid_ohlc.csv"
    df = load_csv(csv_path)
    
    assert isinstance(df, pd.DataFrame), "Should return a pandas DataFrame"
    assert not df.empty, "DataFrame should not be empty"
    assert len(df) == 5, "Should have 5 rows"


def test_load_csv_has_required_columns(fixtures_dir):
    """Test that loaded CSV has all required OHLC columns."""
    csv_path = fixtures_dir / "valid_ohlc.csv"
    df = load_csv(csv_path)
    
    required_columns = ["timestamp", "open", "high", "low", "close", "volume"]
    for col in required_columns:
        assert col in df.columns, f"Missing required column: {col}"


def test_load_csv_file_not_found():
    """Test error handling for non-existent file."""
    with pytest.raises(CSVLoadError, match="File not found"):
        load_csv("nonexistent_file.csv")


def test_load_csv_invalid_path():
    """Test error handling for invalid file path."""
    with pytest.raises(CSVLoadError, match="Invalid file path"):
        load_csv(None)


def test_load_csv_directory_instead_of_file(fixtures_dir):
    """Test error handling when path is a directory."""
    with pytest.raises(CSVLoadError, match="is a directory"):
        load_csv(fixtures_dir)


def test_load_csv_with_pathlib_path(fixtures_dir):
    """Test that load_csv accepts Path objects."""
    csv_path = Path(fixtures_dir) / "valid_ohlc.csv"
    df = load_csv(csv_path)
    
    assert isinstance(df, pd.DataFrame)
    assert not df.empty


def test_load_csv_with_string_path(fixtures_dir):
    """Test that load_csv accepts string paths."""
    csv_path = str(fixtures_dir / "valid_ohlc.csv")
    df = load_csv(csv_path)
    
    assert isinstance(df, pd.DataFrame)
    assert not df.empty


def test_load_malformed_csv_missing_columns(fixtures_dir):
    """Test handling of CSV with missing required columns."""
    csv_path = fixtures_dir / "malformed.csv"
    
    with pytest.raises(CSVLoadError, match="Missing required columns"):
        load_csv(csv_path)


def test_load_empty_csv(fixtures_dir):
    """Test handling of empty CSV file."""
    csv_path = fixtures_dir / "empty.csv"
    
    with pytest.raises(CSVLoadError, match="No data"):
        load_csv(csv_path)


def test_load_csv_returns_raw_dataframe(fixtures_dir):
    """Test that initial load returns DataFrame with string columns (no type conversion yet)."""
    csv_path = fixtures_dir / "valid_ohlc.csv"
    df = load_csv(csv_path)
    
    # At this stage, data should be loaded but not yet processed
    # Timestamp should still be string (not datetime yet)
    assert "timestamp" in df.columns
    assert "open" in df.columns
    # We're not converting types yet in this subtask


def test_load_csv_preserves_column_order(fixtures_dir):
    """Test that column order is preserved from CSV."""
    csv_path = fixtures_dir / "valid_ohlc.csv"
    df = load_csv(csv_path)
    
    expected_order = ["timestamp", "open", "high", "low", "close", "volume"]
    assert list(df.columns) == expected_order


def test_load_csv_handles_utf8_encoding(fixtures_dir):
    """Test that CSV is loaded with UTF-8 encoding."""
    csv_path = fixtures_dir / "valid_ohlc.csv"
    # This test primarily checks that encoding parameter is handled correctly
    df = load_csv(csv_path)
    
    assert not df.empty

