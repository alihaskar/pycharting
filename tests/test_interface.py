"""Tests for Python API interface."""

import pytest
import numpy as np
import time
from unittest.mock import patch, MagicMock

from src.api.interface import plot, stop_server, get_server_status, _active_server
from src.api.routes import _data_managers


@pytest.fixture(autouse=True)
def cleanup_globals():
    """Clean up global state between tests."""
    global _active_server
    
    # Stop any active server before test
    if _active_server and _active_server.is_running:
        _active_server.stop_server()
    
    # Clear data managers
    _data_managers.clear()
    
    yield
    
    # Clean up after test
    if _active_server and _active_server.is_running:
        _active_server.stop_server()
    _data_managers.clear()


class TestPlotFunction:
    """Tests for the main plot() function."""
    
    def test_plot_basic_usage(self):
        """Test basic plot creation with minimal arguments."""
        # Generate sample data
        n = 100
        index = np.arange(n)
        close = np.cumsum(np.random.randn(n)) + 100
        open_data = close + np.random.randn(n) * 0.5
        high = np.maximum(open_data, close) + np.abs(np.random.randn(n))
        low = np.minimum(open_data, close) - np.abs(np.random.randn(n))
        
        # Create chart without opening browser
        result = plot(
            index, open_data, high, low, close,
            open_browser=False
        )
        
        assert result['status'] == 'success'
        assert 'url' in result
        assert result['data_points'] == n
        assert result['server_running'] is True
        assert 'default' in result['session_id']
    
    def test_plot_with_custom_session(self):
        """Test plot with custom session ID."""
        n = 50
        index = np.arange(n)
        data = np.random.randn(n) + 100
        
        result = plot(
            index, data, data + 1, data - 1, data,
            session_id='custom_session',
            open_browser=False
        )
        
        assert result['status'] == 'success'
        assert result['session_id'] == 'custom_session'
        assert 'custom_session' in _data_managers
    
    def test_plot_with_overlays(self):
        """Test plot with overlay data."""
        n = 100
        index = np.arange(n)
        close = np.cumsum(np.random.randn(n)) + 100
        open_data = close + np.random.randn(n) * 0.5
        high = np.maximum(open_data, close) + np.abs(np.random.randn(n))
        low = np.minimum(open_data, close) - np.abs(np.random.randn(n))
        
        # Add moving average overlay
        ma = np.convolve(close, np.ones(10)/10, mode='same')
        
        result = plot(
            index, open_data, high, low, close,
            overlays={'MA10': ma},
            open_browser=False
        )
        
        assert result['status'] == 'success'
        # Check that data manager has overlay
        dm = _data_managers['default']
        assert 'MA10' in dm.overlays
    
    def test_plot_reuses_server(self):
        """Test that multiple plots reuse the same server."""
        n = 50
        data = np.random.randn(n) + 100
        index = np.arange(n)
        
        # First plot
        result1 = plot(
            index, data, data + 1, data - 1, data,
            session_id='session1',
            open_browser=False
        )
        
        first_server_url = result1['server_url']
        
        # Second plot should reuse server
        result2 = plot(
            index, data, data + 1, data - 1, data,
            session_id='session2',
            open_browser=False
        )
        
        assert result2['server_url'] == first_server_url
        assert result1['status'] == 'success'
        assert result2['status'] == 'success'
    
    def test_plot_with_invalid_data(self):
        """Test plot with invalid data returns error."""
        # Try with mismatched array lengths
        result = plot(
            np.arange(10),
            np.random.randn(10),
            np.random.randn(10),
            np.random.randn(10),
            np.random.randn(5),  # Wrong length!
            open_browser=False
        )
        
        assert result['status'] == 'error'
        assert 'error' in result
    
    @patch('webbrowser.open')
    def test_plot_opens_browser(self, mock_browser):
        """Test that plot opens browser when requested."""
        n = 50
        data = np.random.randn(n) + 100
        index = np.arange(n)
        
        result = plot(
            index, data, data + 1, data - 1, data,
            open_browser=True
        )
        
        assert result['status'] == 'success'
        # Check that browser.open was called
        mock_browser.assert_called_once()
        call_args = mock_browser.call_args[0][0]
        assert 'http://' in call_args
    
    @patch('webbrowser.open', side_effect=Exception("Browser error"))
    def test_plot_handles_browser_error(self, mock_browser):
        """Test that plot handles browser opening errors gracefully."""
        n = 50
        data = np.random.randn(n) + 100
        index = np.arange(n)
        
        # Should still succeed even if browser fails
        result = plot(
            index, data, data + 1, data - 1, data,
            open_browser=True
        )
        
        assert result['status'] == 'success'
        assert result['server_running'] is True


class TestStopServer:
    """Tests for stop_server() function."""
    
    def test_stop_server_when_running(self):
        """Test stopping an active server."""
        # Start a server first
        n = 50
        data = np.random.randn(n) + 100
        index = np.arange(n)
        
        plot(index, data, data + 1, data - 1, data, open_browser=False)
        
        # Now stop it
        stop_server()
        
        status = get_server_status()
        assert status['running'] is False
    
    def test_stop_server_when_not_running(self):
        """Test stopping when no server is active."""
        # Should not raise an error
        stop_server()  # Should print info message


class TestGetServerStatus:
    """Tests for get_server_status() function."""
    
    def test_status_when_no_server(self):
        """Test status when no server has been started."""
        status = get_server_status()
        
        assert status['running'] is False
        # server_info may exist from previous server, just check it's not running
        assert status['active_sessions'] == 0
    
    def test_status_when_server_running(self):
        """Test status when server is active."""
        n = 50
        data = np.random.randn(n) + 100
        index = np.arange(n)
        
        # Start server
        plot(index, data, data + 1, data - 1, data, open_browser=False)
        
        status = get_server_status()
        
        assert status['running'] is True
        assert status['server_info'] is not None
        assert status['active_sessions'] >= 1
        assert 'host' in status['server_info']
        assert 'port' in status['server_info']


class TestDataTypes:
    """Tests for different data type inputs."""
    
    def test_plot_with_numpy_arrays(self):
        """Test plot with NumPy arrays."""
        n = 50
        index = np.arange(n)
        close = np.random.randn(n) + 100
        
        result = plot(
            index, close, close + 1, close - 1, close,
            open_browser=False
        )
        
        assert result['status'] == 'success'
    
    def test_plot_with_lists(self):
        """Test plot with Python lists."""
        n = 50
        index = list(range(n))
        close = [100 + i * 0.1 for i in range(n)]
        
        result = plot(
            index, close, 
            [c + 1 for c in close],
            [c - 1 for c in close],
            close,
            open_browser=False
        )
        
        assert result['status'] == 'success'


class TestIntegration:
    """Integration tests for complete workflows."""
    
    def test_full_workflow(self):
        """Test complete workflow: plot -> check status -> stop."""
        # Generate data
        n = 100
        index = np.arange(n)
        close = np.cumsum(np.random.randn(n)) + 100
        open_data = close + np.random.randn(n) * 0.5
        high = np.maximum(open_data, close) + np.abs(np.random.randn(n))
        low = np.minimum(open_data, close) - np.abs(np.random.randn(n))
        
        # 1. Create chart
        result = plot(
            index, open_data, high, low, close,
            session_id='workflow_test',
            open_browser=False
        )
        assert result['status'] == 'success'
        
        # 2. Check status
        status = get_server_status()
        assert status['running'] is True
        assert status['active_sessions'] >= 1
        
        # 3. Stop server
        stop_server()
        
        # 4. Verify stopped
        status = get_server_status()
        assert status['running'] is False
    
    def test_multiple_sessions(self):
        """Test creating multiple chart sessions."""
        n = 50
        data = np.random.randn(n) + 100
        index = np.arange(n)
        
        # Create multiple sessions
        for i in range(3):
            result = plot(
                index, data, data + 1, data - 1, data,
                session_id=f'session_{i}',
                open_browser=False
            )
            assert result['status'] == 'success'
        
        # Check all sessions exist
        assert len(_data_managers) >= 3
        for i in range(3):
            assert f'session_{i}' in _data_managers
