"""
Tests for browser launch utility.
Testing cross-platform browser launching and error handling.
"""

import pytest
from unittest.mock import patch, MagicMock
from charting.browser import (
    launch_browser,
    validate_url,
    is_valid_url,
    launch_browser_with_fallback
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
    @patch('charting.browser.logger')
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


class TestErrorHandlingAndFallback:
    """Test error handling and fallback mechanisms."""
    
    @patch('webbrowser.open', side_effect=Exception("Browser not available"))
    @patch('charting.browser.logger')
    def test_launch_browser_handles_exception(self, mock_logger, mock_open):
        """Test that exceptions during browser launch are handled."""
        url = "http://localhost:3000"
        result = launch_browser(url)
        
        # Should return False on failure
        assert result is False
        
        # Should log warning
        mock_logger.warning.assert_called()
        warning_message = str(mock_logger.warning.call_args)
        assert "Failed to open browser" in warning_message
    
    @patch('webbrowser.open', side_effect=OSError("No browser found"))
    def test_launch_browser_handles_os_error(self, mock_open):
        """Test handling of OSError when browser is unavailable."""
        url = "http://localhost:3000"
        result = launch_browser(url)
        
        assert result is False
    
    @patch('webbrowser.open', side_effect=RuntimeError("Browser launch failed"))
    def test_launch_browser_handles_runtime_error(self, mock_open):
        """Test handling of RuntimeError during browser launch."""
        url = "http://localhost:3000"
        result = launch_browser(url)
        
        assert result is False
    
    @patch('webbrowser.open', side_effect=Exception("Generic error"))
    @patch('charting.browser.logger')
    def test_launch_browser_logs_specific_error_message(self, mock_logger, mock_open):
        """Test that specific error message is logged."""
        url = "http://localhost:3000"
        launch_browser(url)
        
        mock_logger.warning.assert_called()
        warning_message = str(mock_logger.warning.call_args)
        assert "Generic error" in warning_message
    
    @patch('builtins.print')
    @patch('webbrowser.open', side_effect=Exception("Browser not available"))
    def test_fallback_prints_url(self, mock_open, mock_print):
        """Test that fallback mechanism prints URL."""
        url = "http://localhost:3000"
        result = launch_browser_with_fallback(url)
        
        # Should return False (browser launch failed)
        assert result is False
        
        # Should print URL as fallback
        mock_print.assert_called()
        print_message = str(mock_print.call_args)
        assert url in print_message
    
    @patch('builtins.print')
    @patch('webbrowser.open')
    def test_fallback_does_not_print_on_success(self, mock_open, mock_print):
        """Test that fallback does not print when browser launch succeeds."""
        mock_open.return_value = True
        
        url = "http://localhost:3000"
        result = launch_browser_with_fallback(url)
        
        # Should return True (success)
        assert result is True
        
        # Should not print (no fallback needed)
        mock_print.assert_not_called()
    
    @patch('builtins.print')
    @patch('webbrowser.open', side_effect=Exception("Browser not available"))
    def test_fallback_message_format(self, mock_open, mock_print):
        """Test format of fallback message."""
        url = "http://localhost:3000"
        launch_browser_with_fallback(url)
        
        mock_print.assert_called_once()
        print_message = str(mock_print.call_args[0][0])
        assert "Please open your browser to:" in print_message
        assert url in print_message
    
    @patch('builtins.print')
    @patch('webbrowser.open', side_effect=Exception("Error"))
    def test_fallback_with_invalid_url(self, mock_open, mock_print):
        """Test fallback handles invalid URL gracefully."""
        with pytest.raises(ValueError):
            launch_browser_with_fallback("ftp://invalid.com")
        
        # Should not print because validation fails first
        mock_print.assert_not_called()
    
    @patch('webbrowser.open')
    def test_fallback_returns_boolean_status(self, mock_open):
        """Test that fallback returns boolean status."""
        # Test success case
        mock_open.return_value = True
        result = launch_browser_with_fallback("http://localhost:3000")
        assert isinstance(result, bool)
        assert result is True
        
        # Test failure case
        mock_open.side_effect = Exception("Error")
        result = launch_browser_with_fallback("http://localhost:3000")
        assert isinstance(result, bool)
        assert result is False

