"""
Tests for enhanced Charting.load() method

Task 7.1: Test explicit column mappings and indicator classification parameters
"""
import pytest
import pandas as pd
from unittest.mock import patch, MagicMock


class TestEnhancedLoadMethodSignature:
    """Test enhanced load() method accepts new parameters"""
    
    def test_load_accepts_open_parameter(self):
        """load() should accept 'open' column name parameter"""
        from src.python_api.charting import Charting
        import inspect
        
        sig = inspect.signature(Charting.load)
        param_names = list(sig.parameters.keys())
        
        assert 'open' in param_names or 'col_open' in param_names or 'open_col' in param_names, \
            "load() should accept open column parameter"
    
    def test_load_accepts_high_parameter(self):
        """load() should accept 'high' column name parameter"""
        from src.python_api.charting import Charting
        import inspect
        
        sig = inspect.signature(Charting.load)
        param_names = list(sig.parameters.keys())
        
        assert 'high' in param_names or 'col_high' in param_names or 'high_col' in param_names, \
            "load() should accept high column parameter"
    
    def test_load_accepts_low_parameter(self):
        """load() should accept 'low' column name parameter"""
        from src.python_api.charting import Charting
        import inspect
        
        sig = inspect.signature(Charting.load)
        param_names = list(sig.parameters.keys())
        
        assert 'low' in param_names or 'col_low' in param_names or 'low_col' in param_names, \
            "load() should accept low column parameter"
    
    def test_load_accepts_close_parameter(self):
        """load() should accept 'close' column name parameter"""
        from src.python_api.charting import Charting
        import inspect
        
        sig = inspect.signature(Charting.load)
        param_names = list(sig.parameters.keys())
        
        assert 'close' in param_names or 'col_close' in param_names or 'close_col' in param_names, \
            "load() should accept close column parameter"
    
    def test_load_accepts_volume_parameter(self):
        """load() should accept 'volume' column name parameter"""
        from src.python_api.charting import Charting
        import inspect
        
        sig = inspect.signature(Charting.load)
        param_names = list(sig.parameters.keys())
        
        assert 'volume' in param_names or 'col_volume' in param_names or 'volume_col' in param_names, \
            "load() should accept volume column parameter"
    
    def test_load_accepts_indicators_dict(self):
        """load() should accept 'indicators' dict for classification"""
        from src.python_api.charting import Charting
        import inspect
        
        sig = inspect.signature(Charting.load)
        param_names = list(sig.parameters.keys())
        
        assert 'indicators' in param_names, \
            "load() should accept indicators dict parameter"


class TestEnhancedLoadWithCustomColumns:
    """Test load() with explicit column mappings"""
    
    @pytest.fixture
    def sample_df_custom_cols(self):
        """DataFrame with custom column names"""
        dates = pd.date_range('2024-01-01', periods=10, freq='1h')
        return pd.DataFrame({
            'PriceOpen': [100.0 + i for i in range(10)],
            'PriceHigh': [105.0 + i for i in range(10)],
            'PriceLow': [99.0 + i for i in range(10)],
            'PriceClose': [103.0 + i for i in range(10)],
            'Vol': [1000 + i*100 for i in range(10)],
            'rsi_14': [50.0 + i for i in range(10)]
        }, index=dates)
    
    @patch('src.python_api.charting.ServerManager')
    @patch('src.python_api.charting.launch_browser')
    @patch('src.python_api.charting.transform_dataframe_to_csv', return_value='mock.csv')
    def test_load_uses_explicit_column_mapping(
        self, mock_transform, mock_browser, mock_server, sample_df_custom_cols
    ):
        """load() should use explicit column mappings when provided"""
        mock_server_instance = MagicMock()
        mock_server_instance.start.return_value = 'http://test'
        mock_server.return_value = mock_server_instance
        
        from src.python_api.charting import Charting
        
        chart = Charting(auto_open=False)
        
        try:
            # Should use explicit mappings
            url = chart.load(
                sample_df_custom_cols,
                open='PriceOpen',
                high='PriceHigh',
                low='PriceLow',
                close='PriceClose',
                volume='Vol'
            )
            
            # Should succeed without error
            assert url is not None
        finally:
            chart.close()


class TestEnhancedLoadWithIndicatorsDict:
    """Test load() with indicators classification dict"""
    
    @pytest.fixture
    def sample_df_with_indicators(self):
        """DataFrame with multiple indicators"""
        dates = pd.date_range('2024-01-01', periods=10, freq='1h')
        return pd.DataFrame({
            'open': [100.0 + i for i in range(10)],
            'high': [105.0 + i for i in range(10)],
            'low': [99.0 + i for i in range(10)],
            'close': [103.0 + i for i in range(10)],
            'volume': [1000 + i*100 for i in range(10)],
            'sma_20': [102.0 + i for i in range(10)],
            'rsi_14': [50.0 + i for i in range(10)],
            'custom_ind': [1.0 + i for i in range(10)]
        }, index=dates)
    
    @patch('src.python_api.charting.ServerManager')
    @patch('src.python_api.charting.launch_browser')
    @patch('src.python_api.charting.transform_dataframe_to_csv', return_value='mock.csv')
    def test_load_uses_indicators_dict_classification(
        self, mock_transform, mock_browser, mock_server, sample_df_with_indicators
    ):
        """load() should use indicators dict for overlay/subplot classification"""
        mock_server_instance = MagicMock()
        mock_server_instance.start.return_value = 'http://test'
        mock_server.return_value = mock_server_instance
        
        from src.python_api.charting import Charting
        
        chart = Charting(auto_open=False)
        
        try:
            # Use indicators dict: True = overlay, False = subplot
            url = chart.load(
                sample_df_with_indicators,
                indicators={
                    'sma_20': True,       # overlay
                    'rsi_14': False,      # subplot
                    'custom_ind': False   # subplot
                }
            )
            
            assert url is not None
        finally:
            chart.close()


class TestBackwardCompatibility:
    """Test backward compatibility with existing API"""
    
    @pytest.fixture
    def sample_df_standard(self):
        """Standard DataFrame"""
        dates = pd.date_range('2024-01-01', periods=10, freq='1h')
        return pd.DataFrame({
            'open': [100.0 + i for i in range(10)],
            'high': [105.0 + i for i in range(10)],
            'low': [99.0 + i for i in range(10)],
            'close': [103.0 + i for i in range(10)],
            'volume': [1000 + i*100 for i in range(10)]
        }, index=dates)
    
    @patch('src.python_api.charting.ServerManager')
    @patch('src.python_api.charting.launch_browser')
    @patch('src.python_api.charting.transform_dataframe_to_csv', return_value='mock.csv')
    def test_load_works_without_new_parameters(
        self, mock_transform, mock_browser, mock_server, sample_df_standard
    ):
        """load() should still work with just DataFrame (auto-detect)"""
        mock_server_instance = MagicMock()
        mock_server_instance.start.return_value = 'http://test'
        mock_server.return_value = mock_server_instance
        
        from src.python_api.charting import Charting
        
        chart = Charting(auto_open=False)
        
        try:
            # Old API still works
            url = chart.load(sample_df_standard)
            
            assert url is not None
        finally:
            chart.close()
    
    @patch('src.python_api.charting.ServerManager')
    @patch('src.python_api.charting.launch_browser')
    @patch('src.python_api.charting.transform_dataframe_to_csv', return_value='mock.csv')
    def test_load_works_with_overlays_subplots_lists(
        self, mock_transform, mock_browser, mock_server, sample_df_standard
    ):
        """load() should still work with overlays/subplots lists"""
        mock_server_instance = MagicMock()
        mock_server_instance.start.return_value = 'http://test'
        mock_server.return_value = mock_server_instance
        
        from src.python_api.charting import Charting
        
        chart = Charting(auto_open=False)
        
        try:
            # Old API with overlays/subplots
            url = chart.load(sample_df_standard, overlays=[], subplots=[])
            
            assert url is not None
        finally:
            chart.close()

