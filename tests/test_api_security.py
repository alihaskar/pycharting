"""Security tests for API file path validation."""
import pytest
from fastapi.testclient import TestClient
from src.api.main import app
from src.api.processor import validate_filename, sanitize_filename
from pathlib import Path


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


def test_directory_traversal_blocked(client):
    """Test that directory traversal attempts are blocked."""
    malicious_paths = [
        "../../../etc/passwd",
        "..\\..\\..\\windows\\system32\\config\\sam",
        "../../secret.csv",
        ".././../data.csv",
        "folder/../../../secret.csv"
    ]
    
    for path in malicious_paths:
        response = client.get(f"/chart-data?filename={path}")
        assert response.status_code == 400, f"Failed to block: {path}"
        assert "invalid" in response.json()["detail"].lower()


def test_absolute_path_blocked(client):
    """Test that absolute paths are blocked."""
    absolute_paths = [
        "/etc/passwd",
        "C:\\Windows\\System32\\config\\sam",
        "/home/user/secret.csv",
        "C:\\secret.csv"
    ]
    
    for path in absolute_paths:
        response = client.get(f"/chart-data?filename={path}")
        assert response.status_code == 400, f"Failed to block: {path}"


def test_invalid_file_extension_blocked(client):
    """Test that non-CSV files are blocked."""
    invalid_extensions = [
        "malicious.exe",
        "script.sh",
        "data.txt",
        "config.json",
        "image.png",
        "document.pdf"
    ]
    
    for filename in invalid_extensions:
        response = client.get(f"/chart-data?filename={filename}")
        assert response.status_code == 400, f"Failed to block: {filename}"
        assert "extension" in response.json()["detail"].lower()


def test_valid_csv_allowed(client, tmp_path, monkeypatch):
    """Test that valid CSV files are allowed."""
    csv_content = """timestamp,open,high,low,close,volume
2024-01-01 09:00:00,100.0,105.0,95.0,102.0,1000
"""
    csv_file = tmp_path / "valid.csv"
    csv_file.write_text(csv_content)
    
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    
    response = client.get("/chart-data?filename=valid.csv")
    assert response.status_code == 200


def test_sanitize_filename_function():
    """Test the sanitize_filename function."""
    # Valid filenames
    assert sanitize_filename("data.csv") == "data.csv"
    assert sanitize_filename("my-data.csv") == "my-data.csv"
    assert sanitize_filename("data_2024.csv") == "data_2024.csv"
    
    # Invalid characters removed
    assert sanitize_filename("data?.csv") == "data.csv"
    assert sanitize_filename("data*.csv") == "data.csv"
    assert sanitize_filename("data|file.csv") == "datafile.csv"


def test_validate_filename_function():
    """Test the validate_filename function."""
    # Valid filenames
    validate_filename("data.csv")  # Should not raise
    validate_filename("my-data.csv")
    validate_filename("data_2024.csv")
    
    # Invalid filenames should raise ValueError
    with pytest.raises(ValueError, match="traversal"):
        validate_filename("../secret.csv")
    
    with pytest.raises(ValueError, match="absolute"):
        validate_filename("/etc/passwd")
    
    with pytest.raises(ValueError, match="extension"):
        validate_filename("malicious.exe")


def test_null_byte_injection_blocked(client):
    """Test that null byte injection is blocked."""
    malicious = "data.csv%00.exe"
    response = client.get(f"/chart-data?filename={malicious}")
    assert response.status_code == 400


def test_unicode_normalization(client):
    """Test that Unicode tricks are handled."""
    # Right-to-left override
    path = "data\u202e.csv"
    response = client.get(f"/chart-data?filename={path}")
    # Should be blocked
    assert response.status_code == 400


def test_path_length_limit(client):
    """Test that excessively long paths are rejected."""
    long_filename = "a" * 300 + ".csv"
    response = client.get(f"/chart-data?filename={long_filename}")
    assert response.status_code == 400


def test_hidden_file_blocked(client):
    """Test that hidden files are blocked."""
    hidden_files = [
        ".hidden.csv",
        ".env",
        ".gitignore"
    ]
    
    for filename in hidden_files:
        response = client.get(f"/chart-data?filename={filename}")
        assert response.status_code == 400


def test_only_basename_allowed(client):
    """Test that only basenames are allowed (no subdirectories)."""
    paths_with_dirs = [
        "subfolder/data.csv",
        "folder\\data.csv",
        "a/b/c/data.csv"
    ]
    
    for path in paths_with_dirs:
        response = client.get(f"/chart-data?filename={path}")
        assert response.status_code == 400


def test_case_insensitive_csv_extension(client, tmp_path, monkeypatch):
    """Test that .CSV, .Csv, etc. are accepted."""
    for ext in [".CSV", ".Csv", ".csV"]:
        csv_file = tmp_path / f"data{ext}"
        csv_file.write_text("timestamp,open,high,low,close,volume\n2024-01-01,100,105,95,102,1000")
        
        monkeypatch.setenv("DATA_DIR", str(tmp_path))
        response = client.get(f"/chart-data?filename={csv_file.name}")
        assert response.status_code == 200


def test_empty_filename_blocked(client):
    """Test that empty filename is rejected."""
    response = client.get("/chart-data?filename=")
    # Could be 400 (our validation) or 422 (Pydantic validation)
    assert response.status_code in [400, 422]


def test_whitespace_only_filename_blocked(client):
    """Test that whitespace-only filename is rejected."""
    response = client.get("/chart-data?filename=   ")
    assert response.status_code == 400

