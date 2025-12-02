"""
Tests for Single-Command Launcher

Task 8.1-8.4: Launcher script that generates data and opens chart
"""
import pytest
import pandas as pd
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys


class TestLauncherModuleExists:
    """Test launcher module structure"""
    
    def test_launcher_module_exists(self):
        """Should have a launcher module"""
        try:
            from src.charting import launcher
            assert launcher is not None
        except ImportError:
            # Check alternative paths
            from src.charting.launcher import main
            assert main is not None
    
    def test_generate_sample_data_function_exists(self):
        """Should have generate_sample_data function"""
        from src.charting.launcher import generate_sample_data
        assert callable(generate_sample_data)
    
    def test_launch_chart_function_exists(self):
        """Should have launch_chart function"""
        from src.charting.launcher import launch_chart
        assert callable(launch_chart)
    
    def test_main_function_exists(self):
        """Should have main function"""
        from src.charting.launcher import main
        assert callable(main)


class TestGenerateSampleData:
    """Test sample data generation"""
    
    def test_generate_sample_data_returns_dataframe(self):
        """Should return a pandas DataFrame"""
        from src.charting.launcher import generate_sample_data
        
        df = generate_sample_data()
        
        assert isinstance(df, pd.DataFrame)
    
    def test_generate_sample_data_has_ohlc_columns(self):
        """Should have OHLC columns"""
        from src.charting.launcher import generate_sample_data
        
        df = generate_sample_data()
        
        assert 'open' in df.columns or 'Open' in df.columns
        assert 'high' in df.columns or 'High' in df.columns
        assert 'low' in df.columns or 'Low' in df.columns
        assert 'close' in df.columns or 'Close' in df.columns
    
    def test_generate_sample_data_has_indicators(self):
        """Should have indicator columns"""
        from src.charting.launcher import generate_sample_data
        
        df = generate_sample_data()
        cols_lower = [c.lower() for c in df.columns]
        
        # Should have at least one indicator
        has_indicator = any(
            'sma' in c or 'rsi' in c or 'ema' in c or 'macd' in c
            for c in cols_lower
        )
        assert has_indicator, "Should have at least one indicator column"
    
    def test_generate_sample_data_accepts_rows_parameter(self):
        """Should accept rows parameter"""
        from src.charting.launcher import generate_sample_data
        
        # Note: include_indicators=False to avoid warmup period dropping rows
        df = generate_sample_data(rows=50, include_indicators=False)
        
        assert len(df) == 50


class TestLaunchChart:
    """Test chart launching"""
    
    @patch('src.charting.launcher.Charting')
    def test_launch_chart_creates_charting_instance(self, mock_charting_class):
        """Should create Charting instance"""
        mock_chart = MagicMock()
        mock_chart.load.return_value = 'http://test'
        mock_charting_class.return_value = mock_chart
        
        from src.charting.launcher import launch_chart, generate_sample_data
        
        df = generate_sample_data(rows=10)
        launch_chart(df)
        
        mock_charting_class.assert_called_once()
    
    @patch('src.charting.launcher.Charting')
    def test_launch_chart_calls_load(self, mock_charting_class):
        """Should call load() on chart"""
        mock_chart = MagicMock()
        mock_chart.load.return_value = 'http://test'
        mock_charting_class.return_value = mock_chart
        
        from src.charting.launcher import launch_chart, generate_sample_data
        
        df = generate_sample_data(rows=10)
        launch_chart(df)
        
        mock_chart.load.assert_called_once()
    
    @patch('src.charting.launcher.Charting')
    def test_launch_chart_returns_url(self, mock_charting_class):
        """Should return chart URL"""
        mock_chart = MagicMock()
        mock_chart.load.return_value = 'http://localhost:8000/chart'
        mock_charting_class.return_value = mock_chart
        
        from src.charting.launcher import launch_chart, generate_sample_data
        
        df = generate_sample_data(rows=10)
        url = launch_chart(df)
        
        assert url.startswith('http')


class TestMainFunction:
    """Test main entry point"""
    
    @patch('src.charting.launcher.launch_chart')
    @patch('src.charting.launcher.generate_sample_data')
    def test_main_generates_data(self, mock_gen, mock_launch):
        """main() should call generate_sample_data"""
        mock_df = pd.DataFrame({'a': [1]})
        mock_gen.return_value = mock_df
        mock_launch.return_value = 'http://test'
        
        from src.charting.launcher import main
        
        main()
        
        mock_gen.assert_called_once()
    
    @patch('src.charting.launcher.launch_chart')
    @patch('src.charting.launcher.generate_sample_data')
    def test_main_launches_chart(self, mock_gen, mock_launch):
        """main() should call launch_chart"""
        mock_df = pd.DataFrame({'a': [1]})
        mock_gen.return_value = mock_df
        mock_launch.return_value = 'http://test'
        
        from src.charting.launcher import main
        
        main()
        
        mock_launch.assert_called_once()

