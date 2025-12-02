"""
Tests for browser launch utility.
Testing cross-platform browser launching and error handling.
"""

import pytest
from unittest.mock import patch, MagicMock
from src.python_api.browser import (
    launch_browser,
    validate_url,
    is_valid_url
)


class TestURLValidation:
    """Test URL validation functionality."""
    
    def test_validate_url_with_http(self):
        """Test validation of HTTP URLs."""
        url = "http://localhost:3000"
        assert validate_url(url) == url
    
    def test_validate_url_with_https(self):
        """Test validation of HTTPS URLs."""
        url = "https://example.com:8080"
        assert validate_url(url) == url
    
    def test_validate_url_with_port(self):
        """Test validation of URLs with ports."""
        url = "http://localhost:3000"
        assert validate_url(url) == url
    
    def test_validate_url_rejects_invalid_scheme(self):
        """Test rejection of invalid URL schemes."""
        with pytest.raises(ValueError, match="URL must start with http:// or https://"):
            validate_url("ftp://example.com")
    
    def test_validate_url_rejects_no_scheme(self):
        """Test rejection of URLs without scheme."""
        with pytest.raises(ValueError, match="URL must start with http:// or https://"):
            validate_url("localhost:3000")
    
    def test_validate_url_rejects_empty_string(self):
        """Test rejection of empty URL."""
        with pytest.raises(ValueError, match="URL cannot be empty"):
            validate_url("")
    
    def test_validate_url_rejects_whitespace_only(self):
        """Test rejection of whitespace-only URL."""
        with pytest.raises(ValueError, match="URL cannot be empty"):
            validate_url("   ")
    
    def test_is_valid_url_returns_true_for_valid_http(self):
        """Test is_valid_url returns True for valid HTTP URL."""
        assert is_valid_url("http://localhost:3000") is True
    
    def test_is_valid_url_returns_true_for_valid_https(self):
        """Test is_valid_url returns True for valid HTTPS URL."""
        assert is_valid_url("https://example.com") is True
    
    def test_is_valid_url_returns_false_for_invalid(self):
        """Test is_valid_url returns False for invalid URL."""
        assert is_valid_url("ftp://example.com") is False
        assert is_valid_url("localhost:3000") is False
        assert is_valid_url("") is False


class TestCrossPlatformBrowserLaunch:
    """Test cross-platform browser launch functionality."""
    
    @patch('webbrowser.open')
    def test_launch_browser_calls_webbrowser_open(self, mock_open):
        """Test that launch_browser calls webbrowser.open."""
        mock_open.return_value = True
        
        url = "http://localhost:3000"
        result = launch_browser(url)
        
        assert result is True
        mock_open.assert_called_once_with(url, new=2)
    
    @patch('webbrowser.open')
    def test_launch_browser_with_https(self, mock_open):
        """Test browser launch with HTTPS URL."""
        mock_open.return_value = True
        
        url = "https://example.com:8080"
        result = launch_browser(url)
        
        assert result is True
        mock_open.assert_called_once_with(url, new=2)
    
    @patch('webbrowser.open')
    def test_launch_browser_with_localhost(self, mock_open):
        """Test browser launch with localhost."""
        mock_open.return_value = True
        
        url = "http://localhost:3000"
        result = launch_browser(url)
        
        assert result is True
    
    @patch('webbrowser.open')
    def test_launch_browser_with_custom_port(self, mock_open):
        """Test browser launch with custom port."""
        mock_open.return_value = True
        
        url = "http://127.0.0.1:8080"
        result = launch_browser(url)
        
        assert result is True
    
    @patch('webbrowser.open')
    @patch('src.python_api.browser.logger')
    def test_launch_browser_logs_success(self, mock_logger, mock_open):
        """Test that successful launch is logged."""
        mock_open.return_value = True
        
        url = "http://localhost:3000"
        launch_browser(url)
        
        mock_logger.info.assert_called()
        log_message = str(mock_logger.info.call_args)
        assert url in log_message
    
    def test_launch_browser_rejects_invalid_url(self):
        """Test that invalid URL raises ValueError."""
        with pytest.raises(ValueError):
            launch_browser("ftp://invalid.com")
    
    def test_launch_browser_rejects_empty_url(self):
        """Test that empty URL raises ValueError."""
        with pytest.raises(ValueError):
            launch_browser("")
    
    @patch('webbrowser.open')
    def test_launch_browser_with_query_parameters(self, mock_open):
        """Test browser launch with URL query parameters."""
        mock_open.return_value = True
        
        url = "http://localhost:3000?file=data.csv&timeframe=1h"
        result = launch_browser(url)
        
        assert result is True
        mock_open.assert_called_once_with(url, new=2)

