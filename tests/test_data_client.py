"""Tests for data-client.js structure and features."""
import pytest
from pathlib import Path
import re


@pytest.fixture
def data_client_path():
    """Get path to data-client.js."""
    return Path("src/frontend/data-client.js")


@pytest.fixture
def data_client_content(data_client_path):
    """Read data-client.js content."""
    if not data_client_path.exists():
        pytest.skip("data-client.js not found")
    return data_client_path.read_text(encoding='utf-8')


def test_data_client_file_exists(data_client_path):
    """Test that data-client.js exists."""
    assert data_client_path.exists(), "data-client.js should exist"


def test_has_data_client_class(data_client_content):
    """Test that DataClient class is defined."""
    assert re.search(r'class\s+DataClient', data_client_content), \
        "Should define DataClient class"


def test_has_constructor(data_client_content):
    """Test that DataClient has constructor."""
    assert 'constructor(' in data_client_content, \
        "DataClient should have constructor"


def test_has_fetch_chart_data_method(data_client_content):
    """Test that fetchChartData method exists."""
    assert 'fetchChartData' in data_client_content, \
        "Should have fetchChartData method"


def test_uses_async_await(data_client_content):
    """Test that async/await is used for API calls."""
    assert 'async' in data_client_content, \
        "Should use async functions"
    assert 'await' in data_client_content, \
        "Should use await for asynchronous operations"


def test_uses_fetch_api(data_client_content):
    """Test that fetch API is used."""
    assert 'fetch(' in data_client_content, \
        "Should use fetch API for HTTP requests"


def test_has_error_handling(data_client_content):
    """Test that error handling is implemented."""
    has_try_catch = 'try' in data_client_content and 'catch' in data_client_content
    assert has_try_catch, "Should have try-catch error handling"


def test_builds_query_params(data_client_content):
    """Test that query parameter construction is implemented."""
    assert 'URLSearchParams' in data_client_content or 'params' in data_client_content, \
        "Should build query parameters"


def test_handles_indicators_param(data_client_content):
    """Test that indicators parameter is handled."""
    assert 'indicators' in data_client_content.lower(), \
        "Should handle indicators parameter"


def test_handles_timeframe_param(data_client_content):
    """Test that timeframe parameter is handled."""
    assert 'timeframe' in data_client_content.lower(), \
        "Should handle timeframe parameter"


def test_exports_to_window(data_client_content):
    """Test that DataClient is exported to window object."""
    assert 'window.DataClient' in data_client_content, \
        "Should export DataClient to window object"


def test_has_documentation(data_client_content):
    """Test that code has JSDoc comments."""
    assert '/**' in data_client_content or '//' in data_client_content, \
        "Should have code documentation"


def test_validates_response(data_client_content):
    """Test that API response validation is implemented."""
    assert 'response.ok' in data_client_content or 'response.status' in data_client_content, \
        "Should validate HTTP response status"


def test_parses_json_response(data_client_content):
    """Test that JSON response parsing is implemented."""
    assert 'response.json()' in data_client_content or '.json()' in data_client_content, \
        "Should parse JSON responses"


def test_logs_errors(data_client_content):
    """Test that errors are logged."""
    assert 'console.error' in data_client_content or 'console.log' in data_client_content, \
        "Should log errors for debugging"

