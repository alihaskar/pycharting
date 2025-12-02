"""
Tests for main Charting class.
Testing class initialization, configuration, state management, and resource cleanup.
"""

import pytest
import os
import tempfile
from unittest.mock import Mock, patch, MagicMock
from src.python_api.charting import Charting


class TestClassInitialization:
    """Test Task 27.1: Class initialization and configuration."""
    
    def test_charting_default_initialization(self):
        """Test Charting class initializes with default values."""
        chart = Charting()
        
        assert chart.height == 600
        assert chart.port is None
        assert chart.auto_open is True
    
    def test_charting_custom_height(self):
        """Test Charting class with custom height."""
        chart = Charting(height=800)
        
        assert chart.height == 800
    
    def test_charting_custom_port(self):
        """Test Charting class with custom port."""
        chart = Charting(port=9000)
        
        assert chart.port == 9000
    
    def test_charting_auto_open_false(self):
        """Test Charting class with auto_open disabled."""
        chart = Charting(auto_open=False)
        
        assert chart.auto_open is False
    
    def test_charting_all_custom_params(self):
        """Test Charting class with all custom parameters."""
        chart = Charting(height=1000, port=8080, auto_open=False)
        
        assert chart.height == 1000
        assert chart.port == 8080
        assert chart.auto_open is False


class TestStateManagement:
    """Test Task 27.2: State management for server and files."""
    
    def test_charting_initializes_server_manager_none(self):
        """Test server_manager is None on initialization."""
        chart = Charting()
        
        assert chart.server_manager is None
    
    def test_charting_initializes_temp_files_empty(self):
        """Test temp_files list is empty on initialization."""
        chart = Charting()
        
        assert chart.temp_files == []
        assert isinstance(chart.temp_files, list)
    
    def test_cleanup_temp_files_removes_files(self):
        """Test _cleanup_temp_files removes temporary files."""
        chart = Charting()
        
        # Create temporary files
        temp_file1 = tempfile.NamedTemporaryFile(delete=False)
        temp_file2 = tempfile.NamedTemporaryFile(delete=False)
        temp_file1.close()
        temp_file2.close()
        
        chart.temp_files = [temp_file1.name, temp_file2.name]
        
        # Cleanup
        chart._cleanup_temp_files()
        
        # Files should be deleted
        assert not os.path.exists(temp_file1.name)
        assert not os.path.exists(temp_file2.name)
        assert chart.temp_files == []
    
    def test_cleanup_temp_files_handles_missing_files(self):
        """Test _cleanup_temp_files handles files that don't exist."""
        chart = Charting()
        
        chart.temp_files = ['/nonexistent/file1.csv', '/nonexistent/file2.csv']
        
        # Should not raise error
        chart._cleanup_temp_files()
        
        assert chart.temp_files == []
    
    def test_close_method_stops_server(self):
        """Test close() method stops server if running."""
        chart = Charting()
        
        # Mock server manager
        mock_server = Mock()
        mock_server.stop = Mock()
        chart.server_manager = mock_server
        
        chart.close()
        
        # Should have called stop
        mock_server.stop.assert_called_once()
    
    def test_close_method_cleans_temp_files(self):
        """Test close() method cleans up temporary files."""
        chart = Charting()
        
        # Create a temp file
        temp_file = tempfile.NamedTemporaryFile(delete=False)
        temp_file.close()
        chart.temp_files = [temp_file.name]
        
        chart.close()
        
        # File should be deleted
        assert not os.path.exists(temp_file.name)
        assert chart.temp_files == []
    
    def test_close_method_without_server(self):
        """Test close() method works without active server."""
        chart = Charting()
        
        # Should not raise error
        chart.close()
        
        assert chart.server_manager is None


class TestParameterValidation:
    """Test Task 27.3: Parameter validation and error handling."""
    
    def test_charting_validates_height_positive(self):
        """Test height must be positive."""
        with pytest.raises(ValueError, match="Height must be a positive integer"):
            Charting(height=0)
    
    def test_charting_validates_height_negative(self):
        """Test height cannot be negative."""
        with pytest.raises(ValueError, match="Height must be a positive integer"):
            Charting(height=-100)
    
    def test_charting_validates_height_type(self):
        """Test height must be an integer."""
        with pytest.raises(TypeError, match="Height must be an integer"):
            Charting(height="600")
    
    def test_charting_validates_port_range(self):
        """Test port must be in valid range."""
        with pytest.raises(ValueError, match="Port must be between"):
            Charting(port=100)  # Too low
    
    def test_charting_validates_port_upper_range(self):
        """Test port cannot exceed 65535."""
        with pytest.raises(ValueError, match="Port must be between"):
            Charting(port=70000)
    
    def test_charting_validates_port_type(self):
        """Test port must be integer or None."""
        with pytest.raises(TypeError, match="Port must be an integer or None"):
            Charting(port="8000")
    
    def test_charting_validates_auto_open_type(self):
        """Test auto_open must be boolean."""
        with pytest.raises(TypeError, match="auto_open must be a boolean"):
            Charting(auto_open="true")
    
    def test_charting_accepts_none_port(self):
        """Test port=None is valid."""
        chart = Charting(port=None)
        
        assert chart.port is None
    
    def test_charting_accepts_valid_ports(self):
        """Test various valid port numbers."""
        chart1 = Charting(port=1024)
        chart2 = Charting(port=8000)
        chart3 = Charting(port=65535)
        
        assert chart1.port == 1024
        assert chart2.port == 8000
        assert chart3.port == 65535

