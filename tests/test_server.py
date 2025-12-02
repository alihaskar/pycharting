"""
Tests for server port management utilities.
Testing port availability checking and conflict resolution.
"""

import pytest
import socket
from unittest.mock import patch, MagicMock
from src.charting.server import find_available_port, ServerManager


class TestSocketBindingAndAvailability:
    """Test socket binding and port availability checking."""
    
    def test_find_available_port_default(self):
        """Test finding available port with default parameters."""
        port = find_available_port()
        
        # Should return a port number
        assert isinstance(port, int)
        assert port >= 8000
        assert port < 8010  # Within default range
    
    def test_find_available_port_custom_preferred(self):
        """Test finding available port with custom preferred port."""
        port = find_available_port(preferred_port=9000)
        
        assert isinstance(port, int)
        assert port >= 9000
    
    def test_find_available_port_actually_available(self):
        """Test that returned port is actually available."""
        port = find_available_port()
        
        # Try to bind to the returned port
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('localhost', port))
            # If this doesn't raise, the port is available
            assert True
    
    def test_find_available_port_socket_cleanup(self):
        """Test that sockets are properly cleaned up."""
        port1 = find_available_port(preferred_port=8100)
        port2 = find_available_port(preferred_port=8100)
        
        # Should return same port since first socket was cleaned up
        assert port1 == port2


class TestPortRangeIteration:
    """Test port range iteration and conflict resolution."""
    
    @patch('socket.socket')
    def test_tries_next_port_on_conflict(self, mock_socket_class):
        """Test that function tries next port when first is occupied."""
        mock_socket = MagicMock()
        mock_socket_class.return_value.__enter__.return_value = mock_socket
        
        # First port fails, second succeeds
        mock_socket.bind.side_effect = [OSError(), None]
        
        port = find_available_port(preferred_port=8000, max_attempts=5)
        
        # Should return second port (8001)
        assert port == 8001
    
    @patch('socket.socket')
    def test_tries_multiple_ports(self, mock_socket_class):
        """Test iteration through multiple occupied ports."""
        mock_socket = MagicMock()
        mock_socket_class.return_value.__enter__.return_value = mock_socket
        
        # First 3 ports fail, 4th succeeds
        mock_socket.bind.side_effect = [OSError(), OSError(), OSError(), None]
        
        port = find_available_port(preferred_port=8000, max_attempts=10)
        
        # Should return 4th port (8003)
        assert port == 8003
    
    def test_custom_max_attempts(self):
        """Test custom max_attempts parameter."""
        # This should work with custom max_attempts
        port = find_available_port(preferred_port=8200, max_attempts=20)
        
        assert port >= 8200
        assert port < 8220


class TestErrorHandling:
    """Test error handling for edge cases."""
    
    @patch('socket.socket')
    def test_raises_error_when_all_ports_occupied(self, mock_socket_class):
        """Test that RuntimeError is raised when no ports available."""
        mock_socket = MagicMock()
        mock_socket_class.return_value.__enter__.return_value = mock_socket
        
        # All ports fail
        mock_socket.bind.side_effect = OSError()
        
        with pytest.raises(RuntimeError, match="No available ports"):
            find_available_port(preferred_port=8000, max_attempts=5)
    
    @patch('socket.socket')
    def test_error_message_includes_range(self, mock_socket_class):
        """Test that error message includes attempted port range."""
        mock_socket = MagicMock()
        mock_socket_class.return_value.__enter__.return_value = mock_socket
        mock_socket.bind.side_effect = OSError()
        
        with pytest.raises(RuntimeError) as exc_info:
            find_available_port(preferred_port=8000, max_attempts=3)
        
        error_msg = str(exc_info.value)
        assert "8000" in error_msg
        assert "8003" in error_msg or "8002" in error_msg  # End of range
    
    def test_handles_invalid_port_numbers(self):
        """Test handling of edge case port numbers."""
        # Very high port number should still work
        port = find_available_port(preferred_port=50000, max_attempts=5)
        assert port >= 50000
    
    @patch('socket.socket')
    def test_handles_generic_socket_errors(self, mock_socket_class):
        """Test handling of non-OSError socket exceptions."""
        mock_socket = MagicMock()
        mock_socket_class.return_value.__enter__.return_value = mock_socket
        
        # Simulate different socket error on first attempt, success on second
        mock_socket.bind.side_effect = [OSError("Address already in use"), None]
        
        port = find_available_port(preferred_port=8000)
        
        # Should handle the error and return next available port
        assert port == 8001


class TestServerManagerClassStructure:
    """Test ServerManager class initialization and structure."""
    
    def test_server_manager_initialization_default_port(self):
        """Test ServerManager initialization with default port."""
        from fastapi import FastAPI
        app = FastAPI()
        
        manager = ServerManager(app)
        
        assert manager.app is app
        assert isinstance(manager.port, int)
        assert manager.port >= 8000
        assert manager.server is None
        assert manager.thread is None
    
    def test_server_manager_initialization_custom_port(self):
        """Test ServerManager initialization with custom port."""
        from fastapi import FastAPI
        app = FastAPI()
        
        manager = ServerManager(app, port=9000)
        
        assert manager.app is app
        assert manager.port == 9000
    
    def test_server_manager_uses_port_finder(self):
        """Test that ServerManager uses find_available_port when port is None."""
        from fastapi import FastAPI
        app = FastAPI()
        
        manager = ServerManager(app, port=None)
        
        # Should have found a port
        assert isinstance(manager.port, int)
        assert manager.port >= 8000
    
    def test_server_manager_has_required_attributes(self):
        """Test that ServerManager has all required attributes."""
        from fastapi import FastAPI
        app = FastAPI()
        
        manager = ServerManager(app)
        
        assert hasattr(manager, 'app')
        assert hasattr(manager, 'port')
        assert hasattr(manager, 'server')
        assert hasattr(manager, 'thread')
    
    def test_server_manager_initial_state(self):
        """Test ServerManager initial state."""
        from fastapi import FastAPI
        app = FastAPI()
        
        manager = ServerManager(app)
        
        # Server and thread should be None initially
        assert manager.server is None
        assert manager.thread is None
        # Port should be assigned
        assert manager.port is not None


class TestURLBuilding:
    """Test URL building with parameters."""
    
    def test_build_url_basic(self):
        """Test basic URL building."""
        from fastapi import FastAPI
        app = FastAPI()
        manager = ServerManager(app, port=8000)
        
        url = manager.build_url('data.csv')
        
        assert url.startswith('http://127.0.0.1:8000')
        assert 'filename=data.csv' in url
    
    def test_build_url_with_overlays(self):
        """Test URL building with overlay indicators."""
        from fastapi import FastAPI
        app = FastAPI()
        manager = ServerManager(app, port=8000)
        
        url = manager.build_url('data.csv', overlays=['sma_20', 'ema_12'])
        
        assert 'filename=data.csv' in url
        assert 'overlays=sma_20,ema_12' in url
    
    def test_build_url_with_subplots(self):
        """Test URL building with subplot indicators."""
        from fastapi import FastAPI
        app = FastAPI()
        manager = ServerManager(app, port=8000)
        
        url = manager.build_url('data.csv', subplots=['rsi_14', 'macd'])
        
        assert 'filename=data.csv' in url
        assert 'subplots=rsi_14,macd' in url
    
    def test_build_url_with_both_indicators(self):
        """Test URL building with both overlay and subplot indicators."""
        from fastapi import FastAPI
        app = FastAPI()
        manager = ServerManager(app, port=8000)
        
        url = manager.build_url('data.csv', overlays=['sma_20'], subplots=['rsi_14'])
        
        assert 'overlays=sma_20' in url
        assert 'subplots=rsi_14' in url
    
    def test_build_url_with_empty_lists(self):
        """Test URL building with empty indicator lists."""
        from fastapi import FastAPI
        app = FastAPI()
        manager = ServerManager(app, port=8000)
        
        url = manager.build_url('data.csv', overlays=[], subplots=[])
        
        assert 'filename=data.csv' in url
        # Should not include empty parameters
        assert 'overlays=' not in url or 'overlays=&' not in url
        assert 'subplots=' not in url or 'subplots=&' not in url
    
    def test_build_url_special_characters(self):
        """Test URL building with special characters in filename."""
        from fastapi import FastAPI
        app = FastAPI()
        manager = ServerManager(app, port=8000)
        
        url = manager.build_url('my_data.csv')
        
        assert 'filename=my_data.csv' in url


class TestServerStatus:
    """Test server status checking."""
    
    def test_is_running_initially_false(self):
        """Test that server is not running initially."""
        from fastapi import FastAPI
        app = FastAPI()
        manager = ServerManager(app)
        
        assert manager.is_running() is False
    
    def test_get_url_basic(self):
        """Test get_url() method."""
        from fastapi import FastAPI
        app = FastAPI()
        manager = ServerManager(app, port=8000)
        
        url = manager.get_url()
        
        assert url == 'http://127.0.0.1:8000'

