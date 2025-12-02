"""
Tests for python_api public interface.
Testing Task 30: Package initialization and exports.
"""

import pytest


class TestPackageInterface:
    """Test Task 30.1: Package initialization and exports."""
    
    def test_can_import_charting_from_package(self):
        """Test Charting class can be imported from python_api."""
        from charting import Charting
        
        assert Charting is not None
        assert callable(Charting)
    
    def test_can_import_chart_alias(self):
        """Test Chart alias can be imported."""
        from charting import Chart
        
        assert Chart is not None
        assert callable(Chart)
    
    def test_chart_alias_is_charting(self):
        """Test Chart alias points to Charting class."""
        from charting import Charting, Chart
        
        assert Chart is Charting
    
    def test_can_import_utility_functions(self):
        """Test utility functions can be imported."""
        from charting import (
            detect_ohlc_columns,
            classify_indicators,
            transform_dataframe_to_csv
        )
        
        assert callable(detect_ohlc_columns)
        assert callable(classify_indicators)
        assert callable(transform_dataframe_to_csv)
    
    def test_package_has_version(self):
        """Test package has __version__ attribute."""
        import charting as python_api
        
        assert hasattr(python_api, '__version__')
        assert isinstance(python_api.__version__, str)
    
    def test_package_has_all_attribute(self):
        """Test package has __all__ for export control."""
        import charting as python_api
        
        assert hasattr(python_api, '__all__')
        assert isinstance(python_api.__all__, list)
        assert 'Charting' in python_api.__all__
        assert 'Chart' in python_api.__all__
    
    def test_can_instantiate_charting_from_package_import(self):
        """Test can create Charting instance from package import."""
        from charting import Charting
        
        chart = Charting()
        assert chart is not None
        assert chart.height == 600
        assert chart.auto_open is True
        chart.close()
    
    def test_can_use_chart_alias(self):
        """Test can use Chart alias to create instances."""
        from charting import Chart
        
        chart = Chart(height=800)
        assert chart is not None
        assert chart.height == 800
        chart.close()


class TestDependencies:
    """Test Task 30.2: Dependencies are available."""
    
    def test_pandas_available(self):
        """Test pandas is installed and importable."""
        import pandas as pd
        
        assert pd.__version__ >= "1.5.0"
    
    def test_fastapi_available(self):
        """Test fastapi is installed and importable."""
        import fastapi
        
        # FastAPI version should be 0.100.0 or higher
        version_parts = fastapi.__version__.split('.')
        major = int(version_parts[0])
        minor = int(version_parts[1]) if len(version_parts) > 1 else 0
        
        assert major > 0 or minor >= 100
    
    def test_uvicorn_available(self):
        """Test uvicorn is installed and importable."""
        import uvicorn
        
        # Should be importable
        assert uvicorn is not None

