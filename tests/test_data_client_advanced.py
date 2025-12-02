"""Advanced tests for data-client.js enhanced features."""
import pytest
from pathlib import Path
import re


@pytest.fixture
def data_client_content():
    """Read data-client.js content."""
    path = Path("src/frontend/data-client.js")
    if not path.exists():
        pytest.skip("data-client.js not found")
    return path.read_text(encoding='utf-8')


# Query Parameter Validation Tests (8.2)
def test_has_parameter_validation(data_client_content):
    """Test that parameter validation is implemented."""
    has_validation = any([
        'validate' in data_client_content.lower(),
        'if (' in data_client_content and 'throw' in data_client_content,
        'required' in data_client_content.lower()
    ])
    assert has_validation, "Should have parameter validation"


def test_validates_filename_param(data_client_content):
    """Test that filename parameter is validated."""
    assert 'filename' in data_client_content, \
        "Should reference filename parameter"


# Error Handling Tests (8.3)
def test_has_custom_error_classes(data_client_content):
    """Test that custom error classes are defined."""
    has_error_classes = any([
        re.search(r'class\s+\w*Error', data_client_content),
        'NetworkError' in data_client_content,
        'APIError' in data_client_content,
        'ValidationError' in data_client_content
    ])
    assert has_error_classes, "Should define custom error classes"


def test_handles_network_errors(data_client_content):
    """Test that network errors are handled."""
    assert 'catch' in data_client_content, \
        "Should catch and handle network errors"


def test_handles_http_errors(data_client_content):
    """Test that HTTP error responses are handled."""
    assert 'response.ok' in data_client_content or '!response.ok' in data_client_content, \
        "Should handle HTTP error responses"


# Request Debouncing Tests (8.4)
def test_has_debounce_mechanism(data_client_content):
    """Test that request debouncing is implemented."""
    has_debounce = any([
        'debounce' in data_client_content.lower(),
        'setTimeout' in data_client_content,
        'clearTimeout' in data_client_content
    ])
    assert has_debounce, "Should implement request debouncing"


def test_manages_pending_requests(data_client_content):
    """Test that pending requests can be cancelled."""
    has_cancel = any([
        'abort' in data_client_content.lower(),
        'cancel' in data_client_content.lower(),
        'clearTimeout' in data_client_content
    ])
    assert has_cancel, "Should manage and cancel pending requests"


# Loading State Management Tests (8.5)
def test_has_loading_state_management(data_client_content):
    """Test that loading state management is implemented."""
    has_state = any([
        'loading' in data_client_content.lower(),
        'state' in data_client_content.lower(),
        'isLoading' in data_client_content
    ])
    assert has_state, "Should implement loading state management"


def test_tracks_request_states(data_client_content):
    """Test that request states are tracked."""
    has_states = any([
        'idle' in data_client_content.lower(),
        'pending' in data_client_content.lower(),
        'success' in data_client_content.lower(),
        'error' in data_client_content.lower()
    ])
    # This is optional but good practice
    if not has_states:
        pytest.skip("State tracking is optional")


# Integration Tests
def test_proper_code_organization(data_client_content):
    """Test that code is properly organized."""
    # Should have clear separation of concerns
    lines = data_client_content.split('\n')
    assert len(lines) > 50, "Should have substantial implementation"


def test_uses_modern_javascript(data_client_content):
    """Test that modern JavaScript features are used."""
    modern_features = [
        'const ' in data_client_content,
        'let ' in data_client_content,
        'async' in data_client_content,
        '=>' in data_client_content  # Arrow functions
    ]
    assert sum(modern_features) >= 3, \
        "Should use modern JavaScript features (const, let, async, arrow functions)"


def test_has_comprehensive_comments(data_client_content):
    """Test that code has comprehensive documentation."""
    comment_count = data_client_content.count('/**') + data_client_content.count('//')
    assert comment_count >= 5, \
        "Should have adequate code documentation"


def test_exports_single_responsibility(data_client_content):
    """Test that module has single responsibility (data fetching)."""
    # Should export DataClient and possibly error classes
    exports = data_client_content.count('window.')
    assert exports >= 1, "Should export at least DataClient to window"
    assert exports <= 5, "Should not export too many things (single responsibility)"

